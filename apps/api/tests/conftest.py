import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("IEUM_JWT_SECRET", "test-only-secret-at-least-32-characters")
os.environ.setdefault("IEUM_THROTTLE_SECRET", "test-throttle-secret-at-least-32-characters")

from app.db import Base, get_db
from app.main import app
from app.models import Organization, User
from app.security import hash_password


@pytest.fixture
def client(tmp_path) -> Generator[TestClient, None, None]:
    database_path = tmp_path / "ieum-test.db"
    engine = create_engine(
        f"sqlite+pysqlite:///{database_path}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)

    with testing_session() as db:
        donor_org = Organization(id="org-donor", name="정담식당")
        other_donor_org = Organization(id="org-other", name="다른후원처")
        council_org = Organization(id="org-council", name="선부3동 지역사회보장협의체")
        db.add_all(
            [
                donor_org,
                other_donor_org,
                council_org,
                User(
                    id="user-donor",
                    email="donor@ieum.local",
                    password_hash=hash_password("test-password"),
                    name="정담 담당자",
                    role="DONOR",
                    organization_id=donor_org.id,
                    is_active=True,
                ),
                User(
                    id="user-other-donor",
                    email="other-donor@ieum.local",
                    password_hash=hash_password("test-password"),
                    name="다른 후원 담당자",
                    role="DONOR",
                    organization_id=other_donor_org.id,
                    is_active=True,
                ),
                User(
                    id="user-member",
                    email="member@ieum.local",
                    password_hash=hash_password("test-password"),
                    name="김이음",
                    role="MEMBER",
                    organization_id=council_org.id,
                    is_active=True,
                ),
                User(
                    id="user-admin",
                    email="admin@ieum.local",
                    password_hash=hash_password("test-password"),
                    name="운영 담당자",
                    role="ADMIN",
                    organization_id=council_org.id,
                    is_active=True,
                ),
            ]
        )
        db.commit()

    def override_get_db() -> Generator[Session, None, None]:
        with testing_session() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def auth_headers(client: TestClient):
    def login(email: str) -> dict[str, str]:
        response = client.post(
            "/auth/login",
            json={"email": email, "password": "test-password"},
        )
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return login
