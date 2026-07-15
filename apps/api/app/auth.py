import hmac
import os
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from ipaddress import ip_address, ip_network
from math import ceil

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import LoginThrottle, User
from app.schemas import LoginRequest, TokenResponse
from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


LOGIN_WINDOW_SECONDS = 300
ACCOUNT_ATTEMPT_LIMIT = 5
IP_ATTEMPT_LIMIT = 30


def _throttle_secret() -> bytes:
    secret = os.getenv("IEUM_THROTTLE_SECRET")
    if not secret or len(secret) < 32:
        raise RuntimeError("IEUM_THROTTLE_SECRET must be at least 32 characters")
    return secret.encode("utf-8")


def _throttle_key(kind: str, value: str) -> str:
    normalized = value.strip().lower()
    digest = hmac.new(
        _throttle_secret(),
        f"ieum-login-throttle:{kind}\0{normalized}".encode("utf-8"),
        sha256,
    ).hexdigest()
    return f"{kind}:{digest}"


def resolve_client_ip(peer: str, forwarded_for: str | None) -> str:
    configured = os.getenv("IEUM_TRUSTED_PROXY_CIDRS", "")
    networks = [
        ip_network(value.strip(), strict=False)
        for value in configured.split(",")
        if value.strip()
    ]
    try:
        peer_address = ip_address(peer)
    except ValueError:
        return peer
    if not networks or not any(peer_address in network for network in networks):
        return peer
    if not forwarded_for:
        return peer
    chain = [value.strip() for value in forwarded_for.split(",") if value.strip()]
    try:
        addresses = [ip_address(value) for value in chain]
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 전달 IP 헤더입니다.")
    for address in reversed(addresses):
        if not any(address in network for network in networks):
            return str(address)
    return peer


def _increment_throttle(
    db: Session,
    key: str,
    now: datetime,
) -> tuple[int, datetime]:
    table = LoginThrottle.__table__
    cutoff = now - timedelta(seconds=LOGIN_WINDOW_SECONDS)
    dialect_name = db.get_bind().dialect.name
    if dialect_name == "postgresql":
        statement = postgresql_insert(table)
    elif dialect_name == "sqlite":
        statement = sqlite_insert(table)
    else:
        raise RuntimeError(f"지원하지 않는 로그인 제한 DB입니다: {dialect_name}")
    reset_window = table.c.window_started <= cutoff
    statement = (
        statement.values(
            key=key,
            attempt_count=1,
            window_started=now,
            updated_at=now,
        )
        .on_conflict_do_update(
            index_elements=[table.c.key],
            set_={
                "attempt_count": case(
                    (reset_window, 1),
                    else_=table.c.attempt_count + 1,
                ),
                "window_started": case(
                    (reset_window, now),
                    else_=table.c.window_started,
                ),
                "updated_at": now,
            },
        )
        .returning(table.c.attempt_count, table.c.window_started)
    )
    row = db.execute(statement).one_or_none()
    if row is None:
        raise RuntimeError("로그인 제한 카운터를 갱신하지 못했습니다.")
    window_started = row.window_started
    if window_started.tzinfo is None:
        window_started = window_started.replace(tzinfo=timezone.utc)
    else:
        window_started = window_started.astimezone(timezone.utc)
    return int(row.attempt_count), window_started


def _reserve_login_attempt(db: Session, *, email: str, client_ip: str) -> str:
    account_key = _throttle_key("account", email)
    ip_key = _throttle_key("ip", client_ip)
    now = datetime.now(timezone.utc)
    expired_before = now - timedelta(seconds=LOGIN_WINDOW_SECONDS)
    db.execute(
        delete(LoginThrottle).where(LoginThrottle.updated_at <= expired_before)
    )
    account_count, account_window = _increment_throttle(db, account_key, now)
    ip_count, ip_window = _increment_throttle(db, ip_key, now)
    db.commit()
    blocked_windows = []
    if account_count > ACCOUNT_ATTEMPT_LIMIT:
        blocked_windows.append(account_window)
    if ip_count > IP_ATTEMPT_LIMIT:
        blocked_windows.append(ip_window)
    if blocked_windows:
        retry_after = max(
            1,
            ceil(
                max(
                    (
                        window + timedelta(seconds=LOGIN_WINDOW_SECONDS) - now
                    ).total_seconds()
                    for window in blocked_windows
                )
            ),
        )
        raise HTTPException(
            status_code=429,
            detail="로그인 시도가 너무 많습니다. 잠시 후 다시 시도해 주세요.",
            headers={"Retry-After": str(retry_after)},
        )
    return account_key


def _reset_account_throttle(db: Session, account_key: str) -> None:
    db.execute(delete(LoginThrottle).where(LoginThrottle.key == account_key))
    db.commit()


_dummy_password_hash = hash_password("non-user-dummy-password")


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    peer = request.client.host if request.client is not None else "unknown"
    client_key = resolve_client_ip(peer, request.headers.get("x-forwarded-for"))
    normalized_email = payload.email.strip().lower()
    account_key = _reserve_login_attempt(
        db,
        email=normalized_email,
        client_ip=client_key,
    )
    user = db.scalar(select(User).where(User.email == normalized_email))
    candidate_hash = user.password_hash if user is not None else _dummy_password_hash
    password_matches = verify_password(payload.password, candidate_hash)
    if user is None or not user.is_active or not password_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호를 확인해 주세요.",
        )
    _reset_account_throttle(db, account_key)
    token = create_access_token(
        user_id=user.id,
        role=user.role,
        organization_id=user.organization_id,
    )
    return TokenResponse(access_token=token)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    try:
        claims = decode_access_token(credentials.credentials)
    except (jwt.InvalidTokenError, RuntimeError):
        raise HTTPException(status_code=401, detail="유효하지 않은 로그인입니다.")
    user_id = claims.get("sub")
    if not isinstance(user_id, str):
        raise HTTPException(status_code=401, detail="유효하지 않은 로그인입니다.")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="비활성화된 사용자입니다.")
    return user


def require_roles(*roles: str) -> Callable[..., User]:
    def role_dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="이 작업을 수행할 권한이 없습니다.")
        return user

    return role_dependency
