from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agreement import Agreement, AgreementStatus
from app.models.future_modules import LeaseSchedule, Amendment
from app.core.kpi_calculations import calculate_kpis

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/kpis")
def get_kpis(db: Session = Depends(get_db)):
    return calculate_kpis(db)


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    total_agreements = db.query(func.count(Agreement.id)).scalar() or 0
    total_rent = db.query(func.coalesce(func.sum(Agreement.total_rent), 0)).scalar()

    by_status = {
        status.value: db.query(func.count(Agreement.id))
        .filter(Agreement.status == status)
        .scalar()
        or 0
        for status in AgreementStatus
    }

    # --- Portfolio-wide outstanding liability / ROU (as of today) ---
    # Use the closing balance of the most recent period that has already
    # ended - NOT the last period of the whole lease term, which is always
    # zero by design once the lease fully amortizes.
    today = date.today()
    outstanding_liability = 0.0
    outstanding_rou = 0.0
    agreements = db.query(Agreement).filter(Agreement.status != AgreementStatus.TERMINATED).all()
    for agreement in agreements:
        current_period = (
            db.query(LeaseSchedule)
            .filter(LeaseSchedule.agreement_id == agreement.id, LeaseSchedule.period_end < today)
            .order_by(LeaseSchedule.period_number.desc())
            .first()
        )
        if current_period:
            outstanding_liability += float(current_period.closing_liability)
            outstanding_rou += float(current_period.closing_rou)
        else:
            # Lease hasn't started yet (or no completed period so far) -
            # exposure is the initial recognized amount, i.e. period 1's
            # opening balance.
            first_period = (
                db.query(LeaseSchedule)
                .filter(LeaseSchedule.agreement_id == agreement.id)
                .order_by(LeaseSchedule.period_number.asc())
                .first()
            )
            if first_period:
                outstanding_liability += float(first_period.opening_liability)
                outstanding_rou += float(first_period.opening_rou)

    # --- Upcoming expirations (next 90 days) ---
    horizon = today + timedelta(days=90)
    upcoming = (
        db.query(Agreement)
        .filter(
            Agreement.status != AgreementStatus.TERMINATED,
            Agreement.end_date >= today,
            Agreement.end_date <= horizon,
        )
        .order_by(Agreement.end_date.asc())
        .all()
    )
    upcoming_expirations = [
        {
            "id": a.id,
            "urn": a.urn,
            "agreement_name": a.agreement_name,
            "end_date": a.end_date,
            "days_remaining": (a.end_date - today).days,
        }
        for a in upcoming
    ]

    # --- Pending amendments awaiting approval ---
    pending_amendments = (
        db.query(Amendment)
        .filter(Amendment.status == "Pending")
        .order_by(Amendment.created_on.desc())
        .all()
    )
    pending_amendments_count = len(pending_amendments)

    # --- Overdue postings: periods already in the past but never Closed ---
    overdue_postings_count = (
        db.query(func.count(LeaseSchedule.id))
        .filter(LeaseSchedule.period_end < today, LeaseSchedule.status != "Posted")
        .scalar()
        or 0
    )

    return {
        "total_agreements": total_agreements,
        "total_rent": float(total_rent),
        "by_status": by_status,
        "outstanding_liability": round(outstanding_liability, 2),
        "outstanding_rou": round(outstanding_rou, 2),
        "upcoming_expirations": upcoming_expirations,
        "pending_amendments_count": pending_amendments_count,
        "overdue_postings_count": overdue_postings_count,
    }
