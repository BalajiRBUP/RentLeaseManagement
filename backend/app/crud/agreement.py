import uuid
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.agreement import Agreement, AgreementAllocation
from app.models.future_modules import Amendment
from app.schemas.agreement import AgreementCreate, AgreementUpdate
from app.core.calculations import calculate_allocation_amounts


def _generate_urn(db: Session) -> str:
    """AGR-000001, AGR-000002, ... based on row count. Simple and readable;
    swap for a DB sequence if you need it to survive deletes/concurrency at scale."""
    count = db.query(func.count(Agreement.id)).scalar() or 0
    return f"AGR-{count + 1:06d}"


def create_agreement(db: Session, payload: AgreementCreate) -> Agreement:
    agreement = Agreement(
        id=uuid.uuid4(),
        urn=_generate_urn(db),
        agreement_name=payload.agreement_name,
        property_id=payload.property_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        total_rent=payload.total_rent,
        gst_percentage=payload.gst_percentage,
        tds_percentage=payload.tds_percentage,
        payment_frequency=payload.payment_frequency,
        escalation_percentage=payload.escalation_percentage,
        escalation_period=payload.escalation_period,
        discount_rate=payload.discount_rate,
        security_deposit=payload.security_deposit,
        created_by=payload.created_by,
    )

    for alloc in payload.allocations:
        agreement.allocations.append(
            AgreementAllocation(
                id=uuid.uuid4(),
                vendor_id=alloc.vendor_id,
                cost_center_id=alloc.cost_center_id,
                profit_center_id=alloc.profit_center_id,
                split_percentage=alloc.split_percentage,
            )
        )

    db.add(agreement)
    db.commit()
    db.refresh(agreement)
    return agreement


def get_agreement(db: Session, agreement_id: uuid.UUID) -> Agreement | None:
    return (
        db.query(Agreement)
        .options(
            joinedload(Agreement.allocations).joinedload(AgreementAllocation.vendor),
            joinedload(Agreement.allocations).joinedload(AgreementAllocation.cost_center),
            joinedload(Agreement.allocations).joinedload(AgreementAllocation.profit_center),
        )
        .filter(Agreement.id == agreement_id)
        .first()
    )


def list_agreements(db: Session, skip: int = 0, limit: int = 50) -> list[Agreement]:
    return (
        db.query(Agreement)
        .order_by(Agreement.created_on.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def export_agreements_with_amendments(db: Session) -> list[dict]:
    """Return a flat, spreadsheet-ready export. Agreements with multiple
    amendments intentionally produce multiple rows so each amendment is kept."""
    rows = (
        db.query(Agreement, Amendment)
        .outerjoin(Amendment, Amendment.agreement_id == Agreement.id)
        .order_by(Agreement.urn.asc(), Amendment.created_on.asc())
        .all()
    )

    return [
        {
            "agreement_id": agreement.id,
            "agreement_urn": agreement.urn,
            "agreement_name": agreement.agreement_name,
            "property_id": agreement.property_id,
            "start_date": agreement.start_date,
            "end_date": agreement.end_date,
            "total_rent": agreement.total_rent,
            "gst_percentage": agreement.gst_percentage,
            "tds_percentage": agreement.tds_percentage,
            "payment_frequency": agreement.payment_frequency,
            "escalation_percentage": agreement.escalation_percentage,
            "escalation_period": agreement.escalation_period,
            "discount_rate": agreement.discount_rate,
            "security_deposit": agreement.security_deposit,
            "agreement_status": agreement.status,
            "created_by": agreement.created_by,
            "created_on": agreement.created_on,
            "modified_by": agreement.modified_by,
            "modified_on": agreement.modified_on,
            "amendment_id": amendment.id if amendment else None,
            "amendment_type": amendment.amendment_type if amendment else None,
            "amendment_effective_date": amendment.effective_date if amendment else None,
            "amendment_old_value": amendment.old_value if amendment else None,
            "amendment_new_value": amendment.new_value if amendment else None,
            "amendment_status": amendment.status if amendment else None,
            "amendment_requested_by": amendment.requested_by if amendment else None,
            "amendment_approved_by": amendment.approved_by if amendment else None,
            "amendment_approved_on": amendment.approved_on if amendment else None,
            "amendment_created_on": amendment.created_on if amendment else None,
        }
        for agreement, amendment in rows
    ]


def update_agreement(db: Session, agreement_id: uuid.UUID, payload: AgreementUpdate) -> Agreement | None:
    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    if not agreement:
        return None

    update_data = payload.model_dump(exclude_unset=True, exclude={"modified_by"})
    for field, value in update_data.items():
        setattr(agreement, field, value)
    agreement.modified_by = payload.modified_by

    db.commit()
    db.refresh(agreement)
    return agreement


def attach_calculated_amounts(agreement: Agreement) -> Agreement:
    """Populate the non-persisted calculated_* fields on each allocation
    (in place) so the API response includes real numbers, not just splits."""
    for alloc in agreement.allocations:
        amounts = calculate_allocation_amounts(
            total_rent=agreement.total_rent,
            gst_percentage=agreement.gst_percentage,
            tds_percentage=agreement.tds_percentage,
            split_percentage=alloc.split_percentage,
        )
        alloc.calculated_rent = amounts["calculated_rent"]
        alloc.calculated_gst = amounts["calculated_gst"]
        alloc.calculated_tds = amounts["calculated_tds"]
        alloc.net_payable = amounts["net_payable"]
    return agreement
