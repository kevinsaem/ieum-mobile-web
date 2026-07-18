import os

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Organization, User
from app.security import hash_password


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} 환경변수가 필요합니다.")
    return value


def seed_demo() -> None:
    password = required_env("IEUM_DEMO_PASSWORD")

    with SessionLocal() as db:
        donor_org = db.get(Organization, "org-donor")
        if donor_org is None:
            donor_org = Organization(id="org-donor", name="정담식당")
            db.add(donor_org)

        council_org = db.get(Organization, "org-council")
        if council_org is None:
            council_org = Organization(
                id="org-council", name="선부3동 지역사회보장협의체"
            )
            db.add(council_org)
        db.flush()

        demo_users = [
            ("user-donor", "100001", "donor@ieum.local", "정담 담당자", "DONOR", donor_org.id),
            ("user-member", "200001", "member@ieum.local", "김이음", "MEMBER", council_org.id),
            ("user-admin", "900001", "admin@ieum.local", "운영 담당자", "ADMIN", council_org.id),
        ]
        for user_id, login_id, email, name, role, organization_id in demo_users:
            existing = db.scalar(select(User).where(User.email == email))
            if existing is None:
                db.add(
                    User(
                        id=user_id,
                        email=email,
                        login_id=login_id,
                        password_hash=hash_password(password),
                        name=name,
                        role=role,
                        organization_id=organization_id,
                        is_active=True,
                    )
                )
            elif existing.login_id is None:
                existing.login_id = login_id
            elif existing.login_id != login_id:
                raise RuntimeError(f"{email} 계정의 사용자 번호가 예상값과 다릅니다.")
        db.commit()

    print("demo_seed=ready users=3 organizations=2")


if __name__ == "__main__":
    seed_demo()
