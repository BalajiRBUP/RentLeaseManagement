import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.agreement import Agreement
from app.models.future_modules import Amendment
from app.schemas.amendment import AmendmentCreate
from app.core.amendment_engine import snapshot_old_value, apply_amendment, AmendmentError
from app.crud.lease_schedule import rebuild_from_effective_date

RENT_CHANGING_TYPES = {"Rent Increase", "Rent Reduction", "Partial Termination"}


def create_amendment(db: Session, payload: AmendmentCreate) -> Amendment:
    agreement = db.query(Agreement).filter(Agreement.id == payload.agreement_id).first()
    if not agreement:
        raise ValueError("Agreement not found")

    old_value = snapshot_old_value(agreement, payload.amendment_type)

    amendment = Amendment(
        id=uuid.uuid4(),
        agreement_id=payload.agreement_id,
        amendment_type=payload.amendment_type,
        effective_date=payload.effective_date,
        old_value=old_value,
        new_value=payload.new_value,
        status="Pending",
        requested_by=payload.requested_by,
    )
    db.add(amendment)
    db.commit()
    db.refresh(amendment)
    return amendment


def list_amendments_for_agreement(db: Session, agreement_id: uuid.UUID) -> list[Amendment]:
    return (
        db.query(Amendment)
        .filter(Amendment.agreement_id == agreement_id)
        .order_by(Amendment.created_on.desc())
        .all()
    )


def decide_amendment(db: Session, amendment_id: uuid.UUID, decided_by: str, approve: bool) -> Amendment:
    amendment = db.query(Amendment).filter(Amendment.id == amendment_id).first()
    if not amendment:
        raise ValueError("Amendment not found")
    if amendment.status != "Pending":
        raise ValueError(f"Amendment is already {amendment.status}, cannot decide again")

    if not approve:
        amendment.status = "Rejected"
        amendment.approved_by = decided_by
        amendment.approved_on = datetime.utcnow()
        db.commit()
        db.refresh(amendment)
        return amendment

    agreement = db.query(Agreement).filter(Agreement.id == amendment.agreement_id).first()
    if not agreement:
        raise ValueError("Agreement not found")

    # Snapshot the rent as it stood BEFORE this amendment (for first-month
    # blending), only meaningful for amendment types that actually change
    # total_rent - see RENT_CHANGING_TYPES.
    old_total_rent = agreement.total_rent

    # Raises AmendmentError (caller -> 400) on bad new_value; amendment stays
    # Pending so it can be corrected and resubmitted.
    apply_amendment(agreement, amendment.amendment_type, amendment.new_value, amendment.effective_date)

    amendment.status = "Approved"
    amendment.approved_by = decided_by
    amendment.approved_on = datetime.utcnow()
    db.commit()

    old_rent_for_blend = old_total_rent if amendment.amendment_type in RENT_CHANGING_TYPES else agreement.total_rent
    _agreement, liability_adjustment = rebuild_from_effective_date(
        db, agreement, amendment.effective_date, old_total_rent=old_rent_for_blend
    )

    # What Finance needs to post to SAP: the liability/ROU remeasurement
    # amount for a normal amendment, or the write-off amount for a Full
    # Termination. None (e.g. effective date within the first period, so
    # there was nothing to remeasure against) just means nothing to post.
    if liability_adjustment is not None:
        amendment.posting_amount = abs(liability_adjustment)
        amendment.posting_status = "Not Posted"
    db.commit()

    db.refresh(amendment)
    return amendment


def mark_amendment_posted(db: Session, amendment_id: uuid.UUID) -> Amendment:
    amendment = db.query(Amendment).filter(Amendment.id == amendment_id).first()
    if not amendment:
        raise ValueError("Amendment not found")
    if amendment.status != "Approved":
        raise ValueError("Only an Approved amendment can be posted")
    if amendment.posting_amount is None:
        raise ValueError("This amendment has no posting amount (nothing was remeasured)")
    if amendment.posting_status == "Posted":
        raise ValueError("This amendment is already posted")

    amendment.posting_status = "Posted"
    amendment.posted_on = datetime.utcnow()
    db.commit()
    db.refresh(amendment)
    return amendment
