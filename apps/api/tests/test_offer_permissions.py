from fastapi.testclient import TestClient


def test_member_cannot_access_pending_offer_review_queue(
    client: TestClient,
    auth_headers,
) -> None:
    response = client.get(
        "/offers/reviews/pending",
        headers=auth_headers("member@ieum.local"),
    )

    assert response.status_code == 403


def test_donor_cannot_review_offer(
    client: TestClient,
    auth_headers,
) -> None:
    donor_headers = auth_headers("donor@ieum.local")
    created = client.post(
        "/offers",
        headers=donor_headers,
        json={
            "category": "식사",
            "title": "권한 검증 반찬",
            "quantity": 3,
            "unit": "세트",
            "available_until": "2099-12-31",
            "delivery_method": "픽업",
            "description": "권한 검증용 후원입니다.",
        },
    ).json()

    response = client.post(
        f"/offers/{created['id']}/review",
        headers=donor_headers,
        json={
            "action": "APPROVE",
            "reason": "자가 승인 시도",
            "expected_version": created["version"],
        },
    )

    assert response.status_code == 403


def test_member_cannot_access_offer_audit_log(
    client: TestClient,
    auth_headers,
) -> None:
    created = client.post(
        "/offers",
        headers=auth_headers("donor@ieum.local"),
        json={
            "category": "물품",
            "title": "감사 권한 검증 물품",
            "quantity": 2,
            "unit": "개",
            "available_until": "2099-12-31",
            "delivery_method": "방문",
            "description": "감사 로그 접근 권한 검증입니다.",
        },
    ).json()

    response = client.get(
        f"/offers/{created['id']}/audit",
        headers=auth_headers("member@ieum.local"),
    )

    assert response.status_code == 403


def test_anonymous_user_cannot_access_connection_feed(client: TestClient) -> None:
    response = client.get("/offers/available")

    assert response.status_code == 401


def test_other_donor_organization_cannot_modify_offer(
    client: TestClient,
    auth_headers,
) -> None:
    created = client.post(
        "/offers",
        headers=auth_headers("donor@ieum.local"),
        json={
            "category": "서비스",
            "title": "조직 경계 검증 서비스",
            "quantity": 1,
            "unit": "회",
            "available_until": "2099-12-31",
            "delivery_method": "방문",
            "description": "다른 조직 수정 차단 검증입니다.",
        },
    ).json()
    revision = client.post(
        f"/offers/{created['id']}/review",
        headers=auth_headers("admin@ieum.local"),
        json={
            "action": "REQUEST_REVISION",
            "reason": "설명을 보완해 주세요.",
            "expected_version": created["version"],
        },
    ).json()

    response = client.put(
        f"/offers/{created['id']}",
        headers=auth_headers("other-donor@ieum.local"),
        json={
            "category": "서비스",
            "title": "무단 수정 시도",
            "quantity": 1,
            "unit": "회",
            "available_until": "2099-12-31",
            "delivery_method": "방문",
            "description": "다른 조직의 무단 수정 시도입니다.",
            "expected_version": revision["version"],
        },
    )

    assert response.status_code == 403
