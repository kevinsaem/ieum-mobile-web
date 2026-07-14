from enum import StrEnum


class MatchStatus(StrEnum):
    DRAFT = "DRAFT"
    DONOR_CONFIRMATION_PENDING = "DONOR_CONFIRMATION_PENDING"
    DONOR_DECLINED = "DONOR_DECLINED"
    OPS_REVIEW_PENDING = "OPS_REVIEW_PENDING"
    NEEDS_REVISION = "NEEDS_REVISION"
    REJECTED = "REJECTED"
    COUNCIL_APPROVAL_PENDING = "COUNCIL_APPROVAL_PENDING"
    RESERVED = "RESERVED"
    PICKUP_READY = "PICKUP_READY"
    DELIVERY_SCHEDULED = "DELIVERY_SCHEDULED"
    IN_DELIVERY = "IN_DELIVERY"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


_MATCH_TRANSITIONS: dict[MatchStatus, frozenset[MatchStatus]] = {
    MatchStatus.DONOR_CONFIRMATION_PENDING: frozenset(
        {MatchStatus.OPS_REVIEW_PENDING, MatchStatus.DONOR_DECLINED}
    ),
}


def can_match_transition(current: MatchStatus, target: MatchStatus) -> bool:
    return target in _MATCH_TRANSITIONS.get(current, frozenset())


class CaseStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    NEEDS_REVISION = "NEEDS_REVISION"
    CLOSED = "CLOSED"
    APPROVED = "APPROVED"
    SEARCHING = "SEARCHING"
    MATCH_PENDING = "MATCH_PENDING"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    DELIVERY_SCHEDULED = "DELIVERY_SCHEDULED"
    IN_DELIVERY = "IN_DELIVERY"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


_CASE_TRANSITIONS: dict[CaseStatus, frozenset[CaseStatus]] = {
    CaseStatus.PENDING_REVIEW: frozenset({CaseStatus.APPROVED}),
    CaseStatus.APPROVED: frozenset({CaseStatus.SEARCHING}),
}


def can_case_transition(current: CaseStatus, target: CaseStatus) -> bool:
    return target in _CASE_TRANSITIONS.get(current, frozenset())


class OfferStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    NEEDS_REVISION = "NEEDS_REVISION"
    REJECTED = "REJECTED"
    AVAILABLE = "AVAILABLE"
    MATCH_PENDING = "MATCH_PENDING"
    RESERVED = "RESERVED"
    PREPARING_PICKUP = "PREPARING_PICKUP"
    IN_DELIVERY = "IN_DELIVERY"
    PARTIALLY_AVAILABLE = "PARTIALLY_AVAILABLE"
    EXHAUSTED = "EXHAUSTED"
    ARCHIVED = "ARCHIVED"


_OFFER_TRANSITIONS: dict[OfferStatus, frozenset[OfferStatus]] = {
    OfferStatus.PENDING_REVIEW: frozenset(
        {
            OfferStatus.AVAILABLE,
            OfferStatus.NEEDS_REVISION,
            OfferStatus.REJECTED,
        }
    ),
    OfferStatus.NEEDS_REVISION: frozenset({OfferStatus.PENDING_REVIEW}),
}


def can_offer_transition(current: OfferStatus, target: OfferStatus) -> bool:
    return target in _OFFER_TRANSITIONS.get(current, frozenset())
