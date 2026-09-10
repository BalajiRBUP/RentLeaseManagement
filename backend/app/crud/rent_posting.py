import os
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.agreement import Agreement, AgreementAllocation
from app.models.masters import Vendor, Property
from app.models.future_modules import LeaseSchedule, Posting
from app.models.rent_posting import RentPosting
from app.crud.posting import get_filter_data, _generate_document_number

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "rent_invoices")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_rent_cap(db: Session, agreement_id: uuid.UUID, vendor_id: uuid.UUID, period_number: int):
    """This vendor's calculated rent share for this month - the cap the
    invoice amount can never exceed."""
    filter_data = get_filter_data(db, agreement_id, period_number, vendor_id)
    return filter_data["entries"]["Rent"]["period_amount"]


def create_submission(
    db: Session,
    agreement_id: uuid.UUID,
    vendor_id: uuid.UUID,
    period_number: int,
    invoice_amount,
    submitted_by: str,
    file_bytes: bytes,
    file_name: str,
) -> RentPosting:
    already_posted = (
        db.query(Posting)
        .filter(
            Posting.agreement_id == agreement_id,
            Posting.vendor_id == vendor_id,
            Posting.period_number == period_number,
            Posting.posting_type == "Rent",
        )
        .first()
    )
    if already_posted:
        raise ValueError("Rent for this vendor/month has already been posted - no new invoice needed.")

    already_pending = (
        db.query(RentPosting)
        .filter(
            RentPosting.agreement_id == agreement_id,
            RentPosting.vendor_id == vendor_id,
            RentPosting.period_number == period_number,
            RentPosting.status == "Submitted",
        )
        .first()
    )
    if already_pending:
        raise ValueError("An invoice for this vendor/month is already awaiting Finance approval.")

    calculated_rent_amount = get_rent_cap(db, agreement_id, vendor_id, period_number)

    if invoice_amount > calculated_rent_amount:
        raise ValueError(
            f"Invoice amount ({invoice_amount}) cannot exceed this vendor's rent for the month "
            f"({calculated_rent_amount})"
        )
    if invoice_amount <= 0:
        raise ValueError("Invoice amount must be greater than zero")

    safe_name = f"{uuid.uuid4().hex}_{file_name}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    submission = RentPosting(
        id=uuid.uuid4(),
        agreement_id=agreement_id,
        vendor_id=vendor_id,
        period_number=period_number,
        calculated_rent_amount=calculated_rent_amount,
        invoice_amount=invoice_amount,
        invoice_file_name=file_name,
        invoice_file_path=file_path,
        status="Submitted",
        submitted_by=submitted_by,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def _enrich(db: Session, r: RentPosting, include_posting: bool = False) -> dict:
    """Shared enrichment for both the Pending queue and History - full
    agreement details (name, property), the specific vendor on this invoice,
    AND every vendor on the agreement for context (so you can see the whole
    split, not just the one line this invoice covers)."""
    agreement = db.query(Agreement).filter(Agreement.id == r.agreement_id).first()
    vendor = db.query(Vendor).filter(Vendor.id == r.vendor_id).first()
    property_ = db.query(Property).filter(Property.id == agreement.property_id).first() if agreement else None
    period = (
        db.query(LeaseSchedule)
        .filter(LeaseSchedule.agreement_id == r.agreement_id, LeaseSchedule.period_number == r.period_number)
        .first()
    )

    all_allocations = (
        db.query(AgreementAllocation).filter(AgreementAllocation.agreement_id == r.agreement_id).all()
        if agreement
        else []
    )
    all_vendors = []
    for alloc in all_allocations:
        v = db.query(Vendor).filter(Vendor.id == alloc.vendor_id).first()
        if v:
            all_vendors.append(f"{v.vendor_name} ({alloc.split_percentage}%)")

    result = {
        "id": r.id,
        "agreement_id": r.agreement_id,
        "vendor_id": r.vendor_id,
        "period_number": r.period_number,
        "calculated_rent_amount": r.calculated_rent_amount,
        "invoice_amount": r.invoice_amount,
        "invoice_file_name": r.invoice_file_name,
        "status": r.status,
        "submitted_by": r.submitted_by,
        "submitted_on": r.submitted_on,
        "approved_by": r.approved_by,
        "approved_on": r.approved_on,
        "agreement_urn": agreement.urn if agreement else None,
        "agreement_name": agreement.agreement_name if agreement else None,
        "property_name": property_.property_name if property_ else None,
        "vendor_name": vendor.vendor_name if vendor else None,
        "all_vendors_on_agreement": ", ".join(all_vendors) if all_vendors else None,
        "period_start": period.period_start if period else None,
        "period_end": period.period_end if period else None,
    }

    if include_posting:
        posting = (
            db.query(Posting)
            .filter(
                Posting.agreement_id == r.agreement_id,
                Posting.vendor_id == r.vendor_id,
                Posting.period_number == r.period_number,
                Posting.posting_type == "Rent",
            )
            .first()
        )
        result["document_number"] = posting.document_number if posting else None
        result["posted_amount"] = posting.amount if posting else None

    return result


def list_pending(db: Session) -> list[dict]:
    """The Finance SPOC's review queue - every Submitted request, enriched
    with full agreement/vendor/period display info in one pass."""
    rows = db.query(RentPosting).filter(RentPosting.status == "Submitted").order_by(RentPosting.submitted_on.asc()).all()
    return [_enrich(db, r) for r in rows]


def bulk_decide(db: Session, request_ids: list[uuid.UUID], decided_by: str, approve: bool) -> dict:
    succeeded = []
    failed = []

    for rid in request_ids:
        submission = db.query(RentPosting).filter(RentPosting.id == rid).first()
        if not submission:
            failed.append({"id": str(rid), "reason": "Not found"})
            continue
        if submission.status != "Submitted":
            failed.append({"id": str(rid), "reason": f"Already {submission.status}"})
            continue

        if approve:
            already_posted = (
                db.query(Posting)
                .filter(
                    Posting.agreement_id == submission.agreement_id,
                    Posting.vendor_id == submission.vendor_id,
                    Posting.period_number == submission.period_number,
                    Posting.posting_type == "Rent",
                )
                .first()
            )
            if already_posted:
                failed.append({"id": str(rid), "reason": "Rent for this vendor/month was already posted separately"})
                continue

            agreement = db.query(Agreement).filter(Agreement.id == submission.agreement_id).first()
            posting = Posting(
                id=uuid.uuid4(),
                agreement_id=submission.agreement_id,
                vendor_id=submission.vendor_id,
                period_number=submission.period_number,
                posting_type="Rent",
                document_number=_generate_document_number(agreement.urn, submission.period_number, "Rent"),
                amount=submission.invoice_amount,
                status="Posted",
                posted_on=datetime.utcnow(),
            )
            db.add(posting)
            submission.status = "Approved"
        else:
            submission.status = "Rejected"

        submission.approved_by = decided_by
        submission.approved_on = datetime.utcnow()
        succeeded.append(str(rid))

    db.commit()
    return {"succeeded": succeeded, "failed": failed}


def list_history(
    db: Session,
    agreement_id: uuid.UUID | None = None,
    month: str | None = None,  # "YYYY-MM"
) -> list[dict]:
    """Every decided invoice (Approved or Rejected), optionally filtered by
    agreement and/or calendar month - so you can see month-on-month records
    across the whole portfolio, not just one agreement at a time."""
    query = db.query(RentPosting).filter(RentPosting.status.in_(["Approved", "Rejected"]))

    if agreement_id:
        query = query.filter(RentPosting.agreement_id == agreement_id)

    rows = query.order_by(RentPosting.approved_on.desc()).all()
    enriched = [_enrich(db, r, include_posting=True) for r in rows]

    if month:
        enriched = [
            e for e in enriched
            if e["period_start"] and e["period_start"].strftime("%Y-%m") == month
        ]

    return enriched


def list_for_agreement(db: Session, agreement_id: uuid.UUID) -> list[dict]:
    """Every invoice for this agreement, any status - for the Agreement
    Detail page's Rent Payment Details section."""
    rows = (
        db.query(RentPosting)
        .filter(RentPosting.agreement_id == agreement_id)
        .order_by(RentPosting.period_number.asc())
        .all()
    )
    return [_enrich(db, r, include_posting=True) for r in rows]


def get_for_download(db: Session, request_id: uuid.UUID) -> RentPosting | None:
    return db.query(RentPosting).filter(RentPosting.id == request_id).first()
