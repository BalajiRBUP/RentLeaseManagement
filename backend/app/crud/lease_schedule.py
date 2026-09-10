import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.agreement import Agreement
from app.models.future_modules import LeaseSchedule, Amendment
from app.core.lease_calculations import (
    generate_lease_schedule,
    compute_rebuild_start,
    generate_amendment_rebuild,
)


def generate_schedule_for_agreement(db: Session, agreement_id: uuid.UUID) -> Agreement:
    """Full (re)generation - used the first time a schedule is created for an
    agreement, or when there's no amendment history / no frozen periods to
    preserve, so a full rebuild is equivalent anyway."""
    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    if not agreement:
        return None

    db.query(LeaseSchedule).filter(LeaseSchedule.agreement_id == agreement_id).delete()

    periods = generate_lease_schedule(
        start_date=agreement.start_date,
        end_date=agreement.end_date,
        total_rent=agreement.total_rent,
        escalation_percentage=agreement.escalation_percentage,
        escalation_period=agreement.escalation_period,
        discount_rate=agreement.discount_rate,
    )

    for p in periods:
        db.add(_period_to_model(agreement_id, p))

    # Initial Recognition entry (Dr ROU / Cr Lease Liability) - one-time,
    # set fresh every time a FULL generate happens (this is genuinely a new
    # recognition event, e.g. first-ever generate, or a full rebuild that
    # had nothing to preserve). An amendment rebuild that preserves history
    # does NOT go through this function, so it never resets this.
    if periods:
        agreement.recognition_amount = periods[0].opening_liability
        agreement.recognition_status = "Not Posted"
        agreement.recognition_posted_on = None

    db.commit()
    return agreement


def list_schedule_for_agreement(db: Session, agreement_id: uuid.UUID) -> list[LeaseSchedule]:
    return (
        db.query(LeaseSchedule)
        .filter(LeaseSchedule.agreement_id == agreement_id)
        .order_by(LeaseSchedule.period_number.asc())
        .all()
    )


def rebuild_from_effective_date(
    db: Session,
    agreement: Agreement,
    effective_date,
    old_total_rent=None,
) -> tuple:
    """Shared rebuild logic - freezes every period before `effective_date`
    (or the month after the last Posted period, whichever is later) and
    recalculates only from there forward under the agreement's CURRENT
    values.

    Returns (agreement, liability_adjustment). liability_adjustment is None
    when there was nothing to preserve (full regenerate case) since there's
    no "remeasurement" happening in that scenario - the whole schedule is
    just being (re)built from scratch.
    """
    if old_total_rent is None:
        old_total_rent = agreement.total_rent

    existing = list_schedule_for_agreement(db, agreement.id)

    if not existing:
        return generate_schedule_for_agreement(db, agreement.id), None

    last_posted = [p for p in existing if p.status == "Posted"]
    last_posted_month_end = max((p.period_end for p in last_posted), default=None)

    rebuild_start_date = compute_rebuild_start(effective_date, last_posted_month_end)

    frozen = [p for p in existing if p.period_end < rebuild_start_date]

    if not frozen:
        # Effective date falls within (or before) the very first period -
        # nothing meaningful to preserve, equivalent to a full regenerate.
        return generate_schedule_for_agreement(db, agreement.id), None

    last_frozen = frozen[-1]
    starting_period_number = last_frozen.period_number + 1

    periods, liability_adjustment = generate_amendment_rebuild(
        rebuild_start_date=rebuild_start_date,
        lease_end_date=agreement.end_date,
        new_total_rent=agreement.total_rent,
        old_total_rent=old_total_rent,
        escalation_percentage=agreement.escalation_percentage,
        escalation_period=agreement.escalation_period,
        discount_rate=agreement.discount_rate,
        old_opening_liability=last_frozen.closing_liability,
        old_opening_rou=last_frozen.closing_rou,
        starting_period_number=starting_period_number,
        amendment_effective_date=effective_date,
    )

    db.query(LeaseSchedule).filter(
        LeaseSchedule.agreement_id == agreement.id,
        LeaseSchedule.period_number >= starting_period_number,
    ).delete()

    for p in periods:
        db.add(_period_to_model(agreement.id, p, status="Draft"))

    db.commit()
    return agreement, liability_adjustment


def mark_recognition_posted(db: Session, agreement_id: uuid.UUID) -> Agreement:
    """Posts the ONE-TIME initial Recognition entry (Dr ROU / Cr Lease
    Liability) for this agreement. Available as soon as a schedule has been
    generated - does not depend on any period being posted first."""
    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    if not agreement:
        raise ValueError("Agreement not found")
    if agreement.recognition_amount is None:
        raise ValueError("No schedule has been generated yet - nothing to recognize")
    if agreement.recognition_status == "Posted":
        raise ValueError("Recognition has already been posted for this agreement")

    agreement.recognition_status = "Posted"
    agreement.recognition_posted_on = datetime.utcnow()
    db.commit()
    db.refresh(agreement)
    return agreement


def mark_period_posted(db: Session, period_id: uuid.UUID) -> LeaseSchedule | None:
    """The 'Post' button on the Lease Schedule screen. No external SAP call -
    this just records that Recognition (rent), Interest, and Depreciation for
    this period have been posted, using the amounts already calculated on
    the row (lease_payment, interest_expense, depreciation)."""
    period = db.query(LeaseSchedule).filter(LeaseSchedule.id == period_id).first()
    if not period:
        return None
    if period.status == "Posted":
        raise ValueError("This period is already posted")

    period.status = "Posted"
    period.posted_on = datetime.utcnow()
    db.commit()
    db.refresh(period)
    return period


def regenerate_schedule_for_latest_amendment(db: Session, agreement_id: uuid.UUID) -> Agreement:
    """Used by the manual 'Regenerate Schedule' button. If the agreement has
    an approved amendment, rebuilds only from that amendment's effective
    date forward (preserving history). If there's no approved amendment at
    all, does a full regenerate from the agreement's own start date."""
    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    if not agreement:
        raise ValueError("Agreement not found")

    latest_amendment = (
        db.query(Amendment)
        .filter(Amendment.agreement_id == agreement_id, Amendment.status == "Approved")
        .order_by(Amendment.effective_date.desc())
        .first()
    )

    if not latest_amendment:
        return generate_schedule_for_agreement(db, agreement_id)

    agreement, _liability_adjustment = rebuild_from_effective_date(
        db, agreement, latest_amendment.effective_date, old_total_rent=None
    )
    return agreement


def _period_to_model(agreement_id: uuid.UUID, p, status: str = "Draft") -> LeaseSchedule:
    return LeaseSchedule(
        id=uuid.uuid4(),
        agreement_id=agreement_id,
        period_number=p.period_number,
        period_start=p.period_start,
        period_end=p.period_end,
        opening_liability=p.opening_liability,
        interest_expense=p.interest_expense,
        lease_payment=p.lease_payment,
        closing_liability=p.closing_liability,
        opening_rou=p.opening_rou,
        depreciation=p.depreciation,
        closing_rou=p.closing_rou,
        status=status,
    )
