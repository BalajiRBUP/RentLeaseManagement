import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.agreement import Agreement, AgreementAllocation
from app.models.future_modules import LeaseSchedule, Posting

POSTING_TYPES = ["Interest", "Depreciation", "Rent"]

_FIELD_MAP = {
    "Interest": "interest_expense",
    "Depreciation": "depreciation",
    "Rent": "lease_payment",
}

# Interest and Depreciation are always closed together as part of the same
# month-end accounting entry (matches the AS116 script posting both off the
# same TBP row) - one button posts both, but each still gets its own
# document number, same as Rent does independently.
COMBINED_TYPES = ["Interest", "Depreciation"]


def _fy_start(period_start: date) -> date:
    """Indian FY: April 1. If the period falls Jan-Mar, the FY started the
    previous April; if Apr-Dec, it started this year's April."""
    year = period_start.year if period_start.month >= 4 else period_start.year - 1
    return date(year, 4, 1)


def _generate_document_number(agreement_urn: str, period_number: int, posting_type: str) -> str:
    """Simulated JE/document reference - there's no real SAP call here, this
    just gives each posted line a distinct, traceable reference number."""
    return f"JE-{agreement_urn}-P{period_number:03d}-{posting_type[:3].upper()}-{uuid.uuid4().hex[:6].upper()}"


def get_filter_data(db: Session, agreement_id: uuid.UUID, period_number: int, vendor_id: uuid.UUID) -> dict:
    periods = (
        db.query(LeaseSchedule)
        .filter(LeaseSchedule.agreement_id == agreement_id)
        .order_by(LeaseSchedule.period_number.asc())
        .all()
    )
    selected = next((p for p in periods if p.period_number == period_number), None)
    if not selected:
        raise ValueError("Period not found for this agreement")

    allocation = (
        db.query(AgreementAllocation)
        .filter(AgreementAllocation.agreement_id == agreement_id, AgreementAllocation.vendor_id == vendor_id)
        .first()
    )
    if not allocation:
        raise ValueError("This vendor has no allocation on this agreement")

    split = allocation.split_percentage / Decimal("100")
    fy_start_date = _fy_start(selected.period_start)

    ytd_periods = [p for p in periods if fy_start_date <= p.period_start <= selected.period_start]

    result = {}
    for ptype, field in _FIELD_MAP.items():
        period_amount = getattr(selected, field) * split
        ytd_amount = sum((getattr(p, field) for p in ytd_periods), Decimal("0")) * split

        existing = (
            db.query(Posting)
            .filter(
                Posting.agreement_id == agreement_id,
                Posting.vendor_id == vendor_id,
                Posting.period_number == period_number,
                Posting.posting_type == ptype,
            )
            .first()
        )

        result[ptype] = {
            "period_amount": round(period_amount, 2),
            "ytd_amount": round(ytd_amount, 2),
            "posted": existing is not None,
            # The amount/doc number actually recorded at posting time - the
            # authoritative figures once posted, since live YTD could drift
            # if an amendment changes the schedule afterward.
            "posted_amount": existing.amount if existing else None,
            "document_number": existing.document_number if existing else None,
            "posted_on": existing.posted_on if existing else None,
        }

    return {
        "period_number": period_number,
        "period_start": selected.period_start,
        "period_end": selected.period_end,
        "fy_start": fy_start_date,
        "entries": result,
    }


def _create_posting(db: Session, agreement, vendor_id: uuid.UUID, period_number: int, posting_type: str, ytd_amount: Decimal) -> Posting:
    existing = (
        db.query(Posting)
        .filter(
            Posting.agreement_id == agreement.id,
            Posting.vendor_id == vendor_id,
            Posting.period_number == period_number,
            Posting.posting_type == posting_type,
        )
        .first()
    )
    if existing:
        raise ValueError(f"{posting_type} for this vendor/month is already posted")

    posting = Posting(
        id=uuid.uuid4(),
        agreement_id=agreement.id,
        vendor_id=vendor_id,
        period_number=period_number,
        posting_type=posting_type,
        document_number=_generate_document_number(agreement.urn, period_number, posting_type),
        amount=ytd_amount,
        status="Posted",
        posted_on=datetime.utcnow(),
    )
    db.add(posting)
    return posting


def post_entry(db: Session, agreement_id: uuid.UUID, vendor_id: uuid.UUID, period_number: int, posting_type: str) -> Posting:
    if posting_type not in POSTING_TYPES:
        raise ValueError(f"posting_type must be one of: {', '.join(POSTING_TYPES)}")

    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    if not agreement:
        raise ValueError("Agreement not found")

    filter_data = get_filter_data(db, agreement_id, period_number, vendor_id)
    ytd_amount = filter_data["entries"][posting_type]["ytd_amount"]

    posting = _create_posting(db, agreement, vendor_id, period_number, posting_type, ytd_amount)
    db.commit()
    db.refresh(posting)
    return posting


def post_interest_and_depreciation(db: Session, agreement_id: uuid.UUID, vendor_id: uuid.UUID, period_number: int) -> list[Posting]:
    """One action posts BOTH Interest and Depreciation for this vendor/month -
    each still gets its own document number, since they're separate GL lines."""
    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    if not agreement:
        raise ValueError("Agreement not found")

    filter_data = get_filter_data(db, agreement_id, period_number, vendor_id)

    already_posted = [t for t in COMBINED_TYPES if filter_data["entries"][t]["posted"]]
    if already_posted:
        raise ValueError(f"{' and '.join(already_posted)} already posted for this vendor/month")

    postings = []
    for ptype in COMBINED_TYPES:
        ytd_amount = filter_data["entries"][ptype]["ytd_amount"]
        postings.append(_create_posting(db, agreement, vendor_id, period_number, ptype, ytd_amount))

    db.commit()
    for p in postings:
        db.refresh(p)
    return postings
