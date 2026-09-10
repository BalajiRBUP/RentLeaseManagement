import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.lease_schedule import LeaseScheduleSummary
from app.crud import lease_schedule as crud_lease_schedule

router = APIRouter(prefix="/api/lease-schedules", tags=["Lease Schedule"])


@router.post("/generate/{agreement_id}", response_model=LeaseScheduleSummary)
def generate_schedule(agreement_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        agreement = crud_lease_schedule.regenerate_schedule_for_latest_amendment(db, agreement_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    return _build_summary(db, agreement_id)


@router.get("/{agreement_id}", response_model=LeaseScheduleSummary)
def get_schedule(agreement_id: uuid.UUID, db: Session = Depends(get_db)):
    return _build_summary(db, agreement_id)


@router.post("/period/{period_id}/post")
def post_period(period_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        period = crud_lease_schedule.mark_period_posted(db, period_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not period:
        raise HTTPException(status_code=404, detail="Lease schedule period not found")
    return {
        "id": period.id,
        "period_number": period.period_number,
        "status": period.status,
        "posted_on": period.posted_on,
        "recognition_amount": period.lease_payment,
        "interest_amount": period.interest_expense,
        "depreciation_amount": period.depreciation,
    }


@router.post("/{agreement_id}/post-recognition")
def post_recognition(agreement_id: uuid.UUID, db: Session = Depends(get_db)):
    """Posts the ONE-TIME initial Recognition entry (Dr ROU / Cr Lease
    Liability). Available as soon as a schedule exists - not tied to any
    period being posted."""
    try:
        agreement = crud_lease_schedule.mark_recognition_posted(db, agreement_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "recognition_amount": agreement.recognition_amount,
        "recognition_status": agreement.recognition_status,
        "recognition_posted_on": agreement.recognition_posted_on,
    }


def _build_summary(db: Session, agreement_id: uuid.UUID) -> LeaseScheduleSummary:
    from app.models.agreement import Agreement

    agreement = db.query(Agreement).filter(Agreement.id == agreement_id).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")

    periods = crud_lease_schedule.list_schedule_for_agreement(db, agreement_id)

    return LeaseScheduleSummary(
        agreement_id=agreement.id,
        agreement_urn=agreement.urn,
        total_periods=len(periods),
        initial_liability=periods[0].opening_liability if periods else 0,
        initial_rou=periods[0].opening_rou if periods else 0,
        total_interest=sum((p.interest_expense for p in periods), start=0),
        total_depreciation=sum((p.depreciation for p in periods), start=0),
        recognition_amount=agreement.recognition_amount,
        recognition_status=agreement.recognition_status,
        recognition_posted_on=agreement.recognition_posted_on,
        periods=periods,
    )
