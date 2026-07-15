from datetime import date, timedelta

from fastapi.testclient import TestClient
import pytest

import app.offers as offers_module
from app.db import get_db
from app.main import app
from app.models import Offer


def update_offer_for_test(client: TestClient, offer_id: str, **values: object) -> None:
    dependency = app.dependency_overrides[get_db]
    session_iterator = dependency()
    db = next(session_iterator)
    try:
        offer = db.get(Offer, offer_id)
        assert offer is not None
        for key, value in values.items():
            setattr(offer, key, value)
        db.commit()
    finally:
        session_iterator.close()


def offer_payload() -> dict[str, object]:
    return {
        "category": "식사",
        "title": "통합점검 반찬 세트",
        "quantity": 10,
        "unit": "세트",
        "available_until": (date.today() + timedelta(days=30)).isoformat(),
        "delivery_method": "픽업",
        "description": "당일 조리한 반찬 3종 세트입니다.",
    }


def test_donor_registers_offer_as_pending_review(
    client: TestClient,
    auth_headers,
) -> None:
    response = client.post(
        "/offers",
        headers=auth_headers("donor@ieum.local"),
        json=offer_payload(),
    )

    assert response.status_code == 201
    body = response.json()
    assert body.pop("id")
    assert body == {
        "category": "식사",
        "title": "통합점검 반찬 세트",
        "quantity": 10,
        "remaining_quantity": 10,
        "unit": "세트",
        "status": "PENDING_REVIEW",
        "version": 1,
        "organization_id": "org-donor",
        "organization_name": "정담식당",
        "available_until": (date.today() + timedelta(days=30)).isoformat(),
        "delivery_method": "픽업",
        "description": "당일 조리한 반찬 3종 세트입니다.",
        "review_reason": None,
    }


def test_pending_offer_is_hidden_from_member_connection_feed(
    client: TestClient,
    auth_headers,
) -> None:
    create_response = client.post(
        "/offers",
        headers=auth_headers("donor@ieum.local"),
        json=offer_payload(),
    )
    assert create_response.status_code == 201

    feed_response = client.get(
        "/offers/available",
        headers=auth_headers("member@ieum.local"),
    )

    assert feed_response.status_code == 200
    assert feed_response.json() == []


def test_admin_sees_new_offer_in_pending_review_queue(
    client: TestClient,
    auth_headers,
) -> None:
    created = client.post(
        "/offers",
        headers=auth_headers("donor@ieum.local"),
        json=offer_payload(),
    ).json()

    response = client.get(
        "/offers/reviews/pending",
        headers=auth_headers("admin@ieum.local"),
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [created["id"]]
    assert response.json()[0]["status"] == "PENDING_REVIEW"


def test_admin_approval_publishes_offer_to_member_connection_feed(
    client: TestClient,
    auth_headers,
) -> None:
    created = client.post(
        "/offers",
        headers=auth_headers("donor@ieum.local"),
        json=offer_payload(),
    ).json()

    review = client.post(
        f"/offers/{created['id']}/review",
        headers=auth_headers("admin@ieum.local"),
        json={
            "action": "APPROVE",
            "reason": "수량과 기한 확인 완료",
            "expected_version": created["version"],
        },
    )

    assert review.status_code == 200
    assert review.json()["status"] == "AVAILABLE"
    feed = client.get(
        "/offers/available",
        headers=auth_headers("member@ieum.local"),
    )
    assert [item["id"] for item in feed.json()] == [created["id"]]


def test_donor_revises_and_resubmits_same_offer_after_revision_request(
    client: TestClient,
    auth_headers,
) -> None:
    created = client.post(
        "/offers",
        headers=auth_headers("donor@ieum.local"),
        json=offer_payload(),
    ).json()
    requested = client.post(
        f"/offers/{created['id']}/review",
        headers=auth_headers("admin@ieum.local"),
        json={
            "action": "REQUEST_REVISION",
            "reason": "알레르기 안내를 추가해 주세요.",
            "expected_version": created["version"],
        },
    )
    assert requested.status_code == 200
    assert requested.json()["status"] == "NEEDS_REVISION"

    revised_payload = offer_payload() | {
        "description": "당일 조리한 반찬 3종이며 견과류는 포함하지 않습니다.",
        "expected_version": requested.json()["version"],
    }
    resubmitted = client.put(
        f"/offers/{created['id']}",
        headers=auth_headers("donor@ieum.local"),
        json=revised_payload,
    )

    assert resubmitted.status_code == 200
    assert resubmitted.json()["id"] == created["id"]
    assert resubmitted.json()["status"] == "PENDING_REVIEW"
    assert resubmitted.json()["review_reason"] is None
    assert "견과류" in resubmitted.json()["description"]


def test_offer_lifecycle_records_actor_status_reason_and_time(
    client: TestClient,
    auth_headers,
) -> None:
    donor_headers = auth_headers("donor@ieum.local")
    admin_headers = auth_headers("admin@ieum.local")
    created = client.post("/offers", headers=donor_headers, json=offer_payload()).json()
    requested = client.post(
        f"/offers/{created['id']}/review",
        headers=admin_headers,
        json={
            "action": "REQUEST_REVISION",
            "reason": "원재료 안내가 필요합니다.",
            "expected_version": created["version"],
        },
    )
    assert created["version"] == 1
    assert requested.json()["version"] == 2
    resubmitted = client.put(
        f"/offers/{created['id']}",
        headers=donor_headers,
        json=offer_payload()
        | {
            "description": "원재료 안내를 포함한 반찬입니다.",
            "expected_version": requested.json()["version"],
        },
    )
    assert resubmitted.json()["version"] == 3
    approved = client.post(
        f"/offers/{created['id']}/review",
        headers=admin_headers,
        json={
            "action": "APPROVE",
            "reason": "보완 내용 확인 완료",
            "expected_version": resubmitted.json()["version"],
        },
    )
    assert approved.json()["version"] == 4

    response = client.get(
        f"/offers/{created['id']}/audit",
        headers=admin_headers,
    )

    assert response.status_code == 200
    events = response.json()
    assert [event["action"] for event in events] == [
        "CREATED",
        "REVISION_REQUESTED",
        "RESUBMITTED",
        "APPROVED",
    ]
    assert [(event["from_status"], event["to_status"]) for event in events] == [
        (None, "PENDING_REVIEW"),
        ("PENDING_REVIEW", "NEEDS_REVISION"),
        ("NEEDS_REVISION", "PENDING_REVIEW"),
        ("PENDING_REVIEW", "AVAILABLE"),
    ]
    assert events[1]["actor_id"] == "user-admin"
    assert events[1]["reason"] == "원재료 안내가 필요합니다."
    assert all(event["created_at"] for event in events)


def test_donor_cannot_register_offer_with_expired_availability(
    client: TestClient,
    auth_headers,
) -> None:
    payload = offer_payload() | {
        "available_until": (date.today() - timedelta(days=1)).isoformat()
    }

    response = client.post(
        "/offers",
        headers=auth_headers("donor@ieum.local"),
        json=payload,
    )

    assert response.status_code == 422


def test_admin_cannot_approve_offer_that_expired_while_waiting(
    client: TestClient,
    auth_headers,
) -> None:
    created = client.post(
        "/offers",
        headers=auth_headers("donor@ieum.local"),
        json=offer_payload(),
    ).json()
    update_offer_for_test(
        client,
        created["id"],
        available_until=date.today() - timedelta(days=1),
    )

    response = client.post(
        f"/offers/{created['id']}/review",
        headers=auth_headers("admin@ieum.local"),
        json={
            "action": "APPROVE",
            "reason": "검토 완료",
            "expected_version": created["version"],
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "제공 기한이 지나 승인할 수 없습니다."


def test_expired_available_offer_is_hidden_from_connection_feed(
    client: TestClient,
    auth_headers,
) -> None:
    created = client.post(
        "/offers",
        headers=auth_headers("donor@ieum.local"),
        json=offer_payload(),
    ).json()
    approved = client.post(
        f"/offers/{created['id']}/review",
        headers=auth_headers("admin@ieum.local"),
        json={
            "action": "APPROVE",
            "reason": "검토 완료",
            "expected_version": created["version"],
        },
    )
    assert approved.status_code == 200
    update_offer_for_test(
        client,
        created["id"],
        available_until=date.today() - timedelta(days=1),
    )

    response = client.get(
        "/offers/available",
        headers=auth_headers("member@ieum.local"),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_review_rejects_stale_offer_version(
    client: TestClient,
    auth_headers,
) -> None:
    created = client.post(
        "/offers",
        headers=auth_headers("donor@ieum.local"),
        json=offer_payload(),
    ).json()

    response = client.post(
        f"/offers/{created['id']}/review",
        headers=auth_headers("admin@ieum.local"),
        json={
            "action": "APPROVE",
            "reason": "검토 완료",
            "expected_version": 999,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "다른 사용자가 먼저 처리했습니다. 새로고침해 주세요."
    audit = client.get(
        f"/offers/{created['id']}/audit",
        headers=auth_headers("admin@ieum.local"),
    ).json()
    assert [event["action"] for event in audit] == ["CREATED"]


def test_resubmission_rejects_stale_offer_version(
    client: TestClient,
    auth_headers,
) -> None:
    donor_headers = auth_headers("donor@ieum.local")
    admin_headers = auth_headers("admin@ieum.local")
    created = client.post("/offers", headers=donor_headers, json=offer_payload()).json()
    requested = client.post(
        f"/offers/{created['id']}/review",
        headers=admin_headers,
        json={
            "action": "REQUEST_REVISION",
            "reason": "원재료를 보완해 주세요.",
            "expected_version": created["version"],
        },
    ).json()
    assert requested["status"] == "NEEDS_REVISION"

    response = client.put(
        f"/offers/{created['id']}",
        headers=donor_headers,
        json=offer_payload() | {"expected_version": 999},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "다른 사용자가 먼저 처리했습니다. 새로고침해 주세요."


def test_audit_failure_rolls_back_offer_transition(
    client: TestClient,
    auth_headers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    donor_headers = auth_headers("donor@ieum.local")
    admin_headers = auth_headers("admin@ieum.local")
    created = client.post("/offers", headers=donor_headers, json=offer_payload()).json()

    def fail_audit(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated audit failure")

    with monkeypatch.context() as scoped:
        scoped.setattr(offers_module, "add_offer_audit", fail_audit)
        with pytest.raises(RuntimeError, match="simulated audit failure"):
            client.post(
                f"/offers/{created['id']}/review",
                headers=admin_headers,
                json={
                    "action": "APPROVE",
                    "reason": "롤백 검증",
                    "expected_version": created["version"],
                },
            )

    pending = client.get("/offers/reviews/pending", headers=admin_headers).json()
    rolled_back = next(item for item in pending if item["id"] == created["id"])
    assert rolled_back["status"] == "PENDING_REVIEW"
    assert rolled_back["version"] == created["version"]
    audit = client.get(f"/offers/{created['id']}/audit", headers=admin_headers).json()
    assert [event["action"] for event in audit] == ["CREATED"]
