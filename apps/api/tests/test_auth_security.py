from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth import _throttle_key, resolve_client_ip

from app.db import get_db
from app.main import app
from app.models import LoginThrottle


def test_throttle_keys_use_domain_separated_secret_hmac() -> None:
    email = "donor@ieum.local"
    account_key = _throttle_key("account", email)
    ip_key = _throttle_key("ip", email)

    assert account_key == _throttle_key("account", email.upper())
    assert account_key != ip_key
    assert sha256(email.encode("utf-8")).hexdigest() not in account_key


def test_forwarded_ip_is_ignored_from_untrusted_peer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("IEUM_TRUSTED_PROXY_CIDRS", "10.0.0.0/8")
    assert resolve_client_ip("198.51.100.20", "203.0.113.9") == "198.51.100.20"


def test_trusted_proxy_chain_returns_first_untrusted_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("IEUM_TRUSTED_PROXY_CIDRS", "10.0.0.0/8")
    assert resolve_client_ip("10.0.0.1", "203.0.113.9") == "203.0.113.9"
    assert (
        resolve_client_ip("10.0.0.1", "203.0.113.9, 10.0.0.2")
        == "203.0.113.9"
    )


def test_login_rate_limit_blocks_repeated_failures(client: TestClient) -> None:
    payload = {"email": "blocked-user@ieum.local", "password": "wrong-password"}

    for _ in range(5):
        response = client.post("/auth/login", json=payload)
        assert response.status_code == 401

    blocked = client.post("/auth/login", json=payload)

    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"] == "300"
    assert blocked.json()["detail"] == "로그인 시도가 너무 많습니다. 잠시 후 다시 시도해 주세요."


def test_successful_login_resets_failure_count(client: TestClient) -> None:
    invalid = {"email": "donor@ieum.local", "password": "wrong-password"}
    for _ in range(4):
        assert client.post("/auth/login", json=invalid).status_code == 401

    successful = client.post(
        "/auth/login",
        json={"email": "donor@ieum.local", "password": "test-password"},
    )
    assert successful.status_code == 200

    assert client.post("/auth/login", json=invalid).status_code == 401
    assert client.post("/auth/login", json=invalid).status_code == 401


def test_account_limit_is_shared_across_different_ip_addresses(
    client: TestClient,
) -> None:
    payload = {"email": "donor@ieum.local", "password": "wrong-password"}
    clients = [
        TestClient(app, client=(f"10.0.0.{index}", 50000 + index))
        for index in range(1, 4)
    ]
    try:
        for current in clients[:2]:
            assert current.post("/auth/login", json=payload).status_code == 401
            assert current.post("/auth/login", json=payload).status_code == 401
        assert clients[2].post("/auth/login", json=payload).status_code == 401

        blocked = clients[2].post("/auth/login", json=payload)
        assert blocked.status_code == 429
    finally:
        for current in clients:
            current.close()


def test_ip_limit_blocks_many_different_accounts(client: TestClient) -> None:
    for index in range(30):
        response = client.post(
            "/auth/login",
            json={
                "email": f"unknown-{index}@ieum.local",
                "password": "wrong-password",
            },
        )
        assert response.status_code == 401

    blocked = client.post(
        "/auth/login",
        json={"email": "unknown-final@ieum.local", "password": "wrong-password"},
    )
    assert blocked.status_code == 429


def test_parallel_login_attempts_are_atomically_limited(client: TestClient) -> None:
    clients = [
        TestClient(app, client=(f"10.1.0.{index}", 51000 + index))
        for index in range(1, 9)
    ]

    def attempt(current: TestClient) -> int:
        return current.post(
            "/auth/login",
            json={"email": "donor@ieum.local", "password": "wrong-password"},
        ).status_code

    try:
        with ThreadPoolExecutor(max_workers=8) as executor:
            statuses = list(executor.map(attempt, clients))
    finally:
        for current in clients:
            current.close()

    assert sorted(statuses) == [401, 401, 401, 401, 401, 429, 429, 429]


def test_login_limit_window_expires(client: TestClient) -> None:
    payload = {"email": "donor@ieum.local", "password": "wrong-password"}
    for _ in range(5):
        assert client.post("/auth/login", json=payload).status_code == 401
    assert client.post("/auth/login", json=payload).status_code == 429

    dependency = app.dependency_overrides[get_db]
    session_iterator = dependency()
    db = next(session_iterator)
    try:
        expired = datetime.now(timezone.utc) - timedelta(seconds=301)
        for throttle in db.scalars(select(LoginThrottle)).all():
            throttle.window_started = expired
            throttle.updated_at = expired
        db.commit()
    finally:
        session_iterator.close()

    assert client.post("/auth/login", json=payload).status_code == 401

    session_iterator = dependency()
    db = next(session_iterator)
    try:
        active = db.scalars(select(LoginThrottle)).all()
        assert len(active) == 2
        assert all(item.attempt_count == 1 for item in active)
    finally:
        session_iterator.close()
