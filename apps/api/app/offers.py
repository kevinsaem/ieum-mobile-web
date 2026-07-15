from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.db import get_db
from app.models import AuditEvent, Offer, User
from app.schemas import (
    AuditEventRead,
    OfferCreate,
    OfferRead,
    OfferReview,
    OfferRevision,
)
from app.state_machines.workflow import OfferStatus, can_offer_transition

router = APIRouter(prefix="/offers", tags=["offers"])


def add_offer_audit(
    db: Session,
    *,
    offer_id: str,
    action: str,
    from_status: str | None,
    to_status: str,
    actor_id: str,
    reason: str | None = None,
) -> None:
    db.add(
        AuditEvent(
            entity_type="OFFER",
            entity_id=offer_id,
            action=action,
            from_status=from_status,
            to_status=to_status,
            actor_id=actor_id,
            reason=reason,
        )
    )


def offer_read(offer: Offer) -> OfferRead:
    return OfferRead(
        id=offer.id,
        category=offer.category,
        title=offer.title,
        quantity=offer.quantity,
        remaining_quantity=offer.remaining_quantity,
        unit=offer.unit,
        status=offer.status,
        version=offer.version,
        organization_id=offer.organization_id,
        organization_name=offer.organization.name,
        available_until=offer.available_until,
        delivery_method=offer.delivery_method,
        description=offer.description,
        review_reason=offer.review_reason,
    )


@router.get("/reviews/pending", response_model=list[OfferRead])
def list_pending_offer_reviews(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ADMIN")),
) -> list[OfferRead]:
    offers = db.scalars(
        select(Offer)
        .where(Offer.status == OfferStatus.PENDING_REVIEW.value)
        .order_by(Offer.created_at.asc())
    ).all()
    return [offer_read(offer) for offer in offers]


@router.get("/{offer_id}/audit", response_model=list[AuditEventRead])
def list_offer_audit(
    offer_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ADMIN")),
) -> list[AuditEventRead]:
    if db.get(Offer, offer_id) is None:
        raise HTTPException(status_code=404, detail="후원을 찾을 수 없습니다.")
    events = db.scalars(
        select(AuditEvent)
        .where(
            AuditEvent.entity_type == "OFFER",
            AuditEvent.entity_id == offer_id,
        )
        .order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc())
    ).all()
    return [AuditEventRead.model_validate(event) for event in events]


@router.post("/{offer_id}/review", response_model=OfferRead)
def review_offer(
    offer_id: str,
    payload: OfferReview,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ADMIN")),
) -> OfferRead:
    offer = db.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="후원을 찾을 수 없습니다.")
    if offer.version != payload.expected_version:
        raise HTTPException(
            status_code=409,
            detail="다른 사용자가 먼저 처리했습니다. 새로고침해 주세요.",
        )
    target_by_action = {
        "APPROVE": OfferStatus.AVAILABLE,
        "REQUEST_REVISION": OfferStatus.NEEDS_REVISION,
        "REJECT": OfferStatus.REJECTED,
    }
    current = OfferStatus(offer.status)
    target = target_by_action[payload.action]
    if payload.action == "APPROVE" and offer.available_until < date.today():
        raise HTTPException(
            status_code=409,
            detail="제공 기한이 지나 승인할 수 없습니다.",
        )
    if not can_offer_transition(current, target):
        raise HTTPException(status_code=409, detail="현재 상태에서는 검토할 수 없습니다.")
    result = db.execute(
        update(Offer)
        .where(
            Offer.id == offer_id,
            Offer.status == current.value,
            Offer.version == payload.expected_version,
        )
        .values(
            status=target.value,
            review_reason=payload.reason,
            version=Offer.version + 1,
        )
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="다른 사용자가 먼저 처리했습니다. 새로고침해 주세요.",
        )
    action_by_review = {
        "APPROVE": "APPROVED",
        "REQUEST_REVISION": "REVISION_REQUESTED",
        "REJECT": "REJECTED",
    }
    add_offer_audit(
        db,
        offer_id=offer.id,
        action=action_by_review[payload.action],
        from_status=current.value,
        to_status=target.value,
        actor_id=_admin.id,
        reason=payload.reason,
    )
    db.commit()
    db.refresh(offer)
    return offer_read(offer)


@router.get("/available", response_model=list[OfferRead])
def list_available_offers(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("MEMBER", "ADMIN")),
) -> list[OfferRead]:
    offers = db.scalars(
        select(Offer)
        .where(
            Offer.status == OfferStatus.AVAILABLE.value,
            Offer.available_until >= date.today(),
        )
        .order_by(Offer.created_at.desc())
    ).all()
    return [offer_read(offer) for offer in offers]


@router.put("/{offer_id}", response_model=OfferRead)
def revise_offer(
    offer_id: str,
    payload: OfferRevision,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("DONOR")),
) -> OfferRead:
    offer = db.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="후원을 찾을 수 없습니다.")
    if offer.organization_id != user.organization_id:
        raise HTTPException(status_code=403, detail="다른 조직의 후원을 수정할 수 없습니다.")
    if offer.version != payload.expected_version:
        raise HTTPException(
            status_code=409,
            detail="다른 사용자가 먼저 처리했습니다. 새로고침해 주세요.",
        )
    current = OfferStatus(offer.status)
    if not can_offer_transition(current, OfferStatus.PENDING_REVIEW):
        raise HTTPException(status_code=409, detail="보완 요청된 후원만 재제출할 수 있습니다.")
    result = db.execute(
        update(Offer)
        .where(
            Offer.id == offer_id,
            Offer.organization_id == user.organization_id,
            Offer.status == current.value,
            Offer.version == payload.expected_version,
        )
        .values(
            category=payload.category,
            title=payload.title,
            quantity=payload.quantity,
            remaining_quantity=payload.quantity,
            unit=payload.unit,
            available_until=payload.available_until,
            delivery_method=payload.delivery_method,
            description=payload.description,
            status=OfferStatus.PENDING_REVIEW.value,
            review_reason=None,
            version=Offer.version + 1,
        )
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="다른 사용자가 먼저 처리했습니다. 새로고침해 주세요.",
        )
    add_offer_audit(
        db,
        offer_id=offer.id,
        action="RESUBMITTED",
        from_status=current.value,
        to_status=OfferStatus.PENDING_REVIEW.value,
        actor_id=user.id,
    )
    db.commit()
    db.refresh(offer)
    return offer_read(offer)


@router.post("", response_model=OfferRead, status_code=201)
def create_offer(
    payload: OfferCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("DONOR")),
) -> OfferRead:
    if not user.organization_id:
        raise RuntimeError("후원자에게 조직이 지정되지 않았습니다.")
    offer = Offer(
        organization_id=user.organization_id,
        created_by=user.id,
        category=payload.category,
        title=payload.title,
        quantity=payload.quantity,
        remaining_quantity=payload.quantity,
        unit=payload.unit,
        available_until=payload.available_until,
        delivery_method=payload.delivery_method,
        description=payload.description,
        status=OfferStatus.PENDING_REVIEW.value,
    )
    db.add(offer)
    db.flush()
    add_offer_audit(
        db,
        offer_id=offer.id,
        action="CREATED",
        from_status=None,
        to_status=OfferStatus.PENDING_REVIEW.value,
        actor_id=user.id,
    )
    db.commit()
    db.refresh(offer)
    return offer_read(offer)
