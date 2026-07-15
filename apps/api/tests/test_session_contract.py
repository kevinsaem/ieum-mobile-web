from fastapi.testclient import TestClient

from app.security import decode_access_token


def test_access_token_lifetime_is_at_most_30_minutes(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "donor@ieum.local", "password": "test-password"},
    )
    claims = decode_access_token(response.json()["access_token"])

    assert int(claims["exp"]) - int(claims["iat"]) <= 30 * 60


def test_login_returns_role_aware_session(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "donor@ieum.local", "password": "test-password"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"] == {
        "id": "user-donor",
        "name": "정담 담당자",
        "role": "DONOR",
        "organization_id": "org-donor",
        "organization_name": "정담식당",
    }


def test_donor_lists_only_own_organization_offers(
    client: TestClient,
    auth_headers,
) -> None:
    donor_headers = auth_headers("donor@ieum.local")
    other_headers = auth_headers("other-donor@ieum.local")
    payload = {
        "category": "식사",
        "title": "내 후원 반찬",
        "quantity": 5,
        "unit": "세트",
        "available_until": "2099-12-31",
        "delivery_method": "픽업",
        "description": "내 조직 후원입니다.",
    }
    mine = client.post("/offers", headers=donor_headers, json=payload).json()
    client.post(
        "/offers",
        headers=other_headers,
        json=payload | {"title": "다른 조직 후원"},
    )

    response = client.get("/offers/mine", headers=donor_headers)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [mine["id"]]


def test_local_web_origin_is_allowed_by_cors(client: TestClient) -> None:
    response = client.options(
        "/auth/login",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
