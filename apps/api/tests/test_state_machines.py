from app.state_machines.workflow import (
    CaseStatus,
    MatchStatus,
    OfferStatus,
    can_case_transition,
    can_match_transition,
    can_offer_transition,
)


def test_pending_offer_can_be_approved_as_available() -> None:
    assert can_offer_transition(
        OfferStatus.PENDING_REVIEW,
        OfferStatus.AVAILABLE,
    )


def test_pending_offer_can_request_revision_or_be_rejected() -> None:
    assert can_offer_transition(
        OfferStatus.PENDING_REVIEW,
        OfferStatus.NEEDS_REVISION,
    )
    assert can_offer_transition(
        OfferStatus.PENDING_REVIEW,
        OfferStatus.REJECTED,
    )


def test_revised_offer_can_be_resubmitted_for_review() -> None:
    assert can_offer_transition(
        OfferStatus.NEEDS_REVISION,
        OfferStatus.PENDING_REVIEW,
    )


def test_approved_case_can_enter_resource_search() -> None:
    assert can_case_transition(
        CaseStatus.PENDING_REVIEW,
        CaseStatus.APPROVED,
    )
    assert can_case_transition(
        CaseStatus.APPROVED,
        CaseStatus.SEARCHING,
    )


def test_donor_confirmation_is_required_before_operations_review() -> None:
    assert can_match_transition(
        MatchStatus.DONOR_CONFIRMATION_PENDING,
        MatchStatus.OPS_REVIEW_PENDING,
    )
