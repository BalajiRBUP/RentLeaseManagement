"""
IND AS 116 KPI calculations, per the BRD reference table:
  1. ROU Asset Value (Gross)
  2. ROU Asset Net Book Value (NBV)
  3. Lease Liability (Closing Balance)
  4. Lease Liability Split (Current vs Non-current)
  5. Interest Expense on Lease Liability (Current Month / YTD)
  6. Depreciation on ROU Asset (Current Month / YTD)
  7. Lease Liability Movement
  8. ROU Movement (including additions/deletions detection)
  9. Ind AS 116 Applicability Coverage %

Additions/deletions detection (KPI 8): rather than a separate flag, we
compare each period's opening_rou against the PREVIOUS period's
closing_rou. In ordinary month-to-month amortization these are always
equal. Any mismatch is exactly the remeasurement jump caused by an
approved amendment - positive = addition, negative = deletion. This
avoids needing a new signed column anywhere; it falls straight out of
the schedule data already stored.
"""
from datetime import date, timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.models.agreement import Agreement, AgreementStatus
from app.models.future_modules import LeaseSchedule


def _fy_start(d: date) -> date:
    year = d.year if d.month >= 4 else d.year - 1
    return date(year, 4, 1)


def _period_covering(periods: list[LeaseSchedule], target: date) -> LeaseSchedule | None:
    """The period whose date range contains `target`, or the closest
    completed period before it if none contains it exactly."""
    covering = [p for p in periods if p.period_start <= target <= p.period_end]
    if covering:
        return covering[0]
    before = [p for p in periods if p.period_end < target]
    return before[-1] if before else None


def calculate_kpis(db: Session) -> dict:
    today = date.today()
    fy_start_date = _fy_start(today)
    twelve_months_out = today + relativedelta(months=12)

    active_agreements = db.query(Agreement).filter(Agreement.status != AgreementStatus.TERMINATED).all()

    rou_gross = Decimal("0")
    rou_nbv = Decimal("0")
    liability_closing = Decimal("0")
    liability_current = Decimal("0")
    liability_noncurrent = Decimal("0")

    interest_current_month = Decimal("0")
    interest_ytd = Decimal("0")
    depreciation_current_month = Decimal("0")
    depreciation_ytd = Decimal("0")

    movement_opening = Decimal("0")
    movement_interest = Decimal("0")
    movement_payment = Decimal("0")
    movement_closing = Decimal("0")

    rou_movement_opening = Decimal("0")
    rou_movement_depreciation = Decimal("0")
    rou_movement_additions = Decimal("0")
    rou_movement_deletions = Decimal("0")
    rou_movement_closing = Decimal("0")

    # last 12 calendar months, portfolio-wide, for the trend chart
    trend_months = [(today.replace(day=1) - relativedelta(months=i)) for i in range(11, -1, -1)]
    trend = {m: {"interest": Decimal("0"), "depreciation": Decimal("0")} for m in trend_months}

    for agreement in active_agreements:
        periods = (
            db.query(LeaseSchedule)
            .filter(LeaseSchedule.agreement_id == agreement.id)
            .order_by(LeaseSchedule.period_number.asc())
            .all()
        )
        if not periods:
            continue

        # --- KPI 1: Gross ROU (recognition amount, the original commencement value) ---
        if agreement.recognition_amount is not None:
            rou_gross += agreement.recognition_amount
        else:
            rou_gross += periods[0].opening_rou

        # --- KPI 2 & 3: NBV and liability closing, as of today ---
        current_period = _period_covering(periods, today)
        if current_period:
            rou_nbv += current_period.closing_rou
            liability_closing += current_period.closing_liability

            # --- KPI 4: Current vs Non-current split ---
            future_period = _period_covering(periods, twelve_months_out)
            noncurrent_amount = future_period.closing_liability if future_period else Decimal("0")
            liability_noncurrent += noncurrent_amount
            liability_current += (current_period.closing_liability - noncurrent_amount)

            # --- KPI 7: Liability movement for the current month ---
            movement_opening += current_period.opening_liability
            movement_interest += current_period.interest_expense
            movement_payment += current_period.lease_payment
            movement_closing += current_period.closing_liability

            # --- KPI 8: ROU movement for the current month ---
            rou_movement_opening += current_period.opening_rou
            rou_movement_depreciation += current_period.depreciation
            rou_movement_closing += current_period.closing_rou

            prev_period = next((p for p in periods if p.period_number == current_period.period_number - 1), None)
            if prev_period is not None:
                jump = current_period.opening_rou - prev_period.closing_rou
                if jump > 0:
                    rou_movement_additions += jump
                elif jump < 0:
                    rou_movement_deletions += jump

        # --- KPI 5 & 6: interest/depreciation this month, YTD, and 12-month trend ---
        for p in periods:
            if p.period_start.replace(day=1) == today.replace(day=1):
                interest_current_month += p.interest_expense
                depreciation_current_month += p.depreciation
            if fy_start_date <= p.period_start <= today:
                interest_ytd += p.interest_expense
                depreciation_ytd += p.depreciation
            month_key = p.period_start.replace(day=1)
            if month_key in trend:
                trend[month_key]["interest"] += p.interest_expense
                trend[month_key]["depreciation"] += p.depreciation

    # --- KPI 9: Ind AS 116 applicability coverage ---
    total_agreements = db.query(Agreement).count()
    recognized_count = db.query(Agreement).filter(Agreement.recognition_status == "Posted").count()
    coverage_percentage = round((recognized_count / total_agreements) * 100, 2) if total_agreements else 0.0

    return {
        "rou_gross": round(rou_gross, 2),
        "rou_nbv": round(rou_nbv, 2),
        "liability_closing": round(liability_closing, 2),
        "liability_current": round(liability_current, 2),
        "liability_noncurrent": round(liability_noncurrent, 2),
        "interest_current_month": round(interest_current_month, 2),
        "interest_ytd": round(interest_ytd, 2),
        "depreciation_current_month": round(depreciation_current_month, 2),
        "depreciation_ytd": round(depreciation_ytd, 2),
        "liability_movement": {
            "opening": round(movement_opening, 2),
            "interest": round(movement_interest, 2),
            "payment": round(movement_payment, 2),
            "closing": round(movement_closing, 2),
        },
        "rou_movement": {
            "opening": round(rou_movement_opening, 2),
            "depreciation": round(rou_movement_depreciation, 2),
            "additions": round(rou_movement_additions, 2),
            "deletions": round(rou_movement_deletions, 2),
            "closing": round(rou_movement_closing, 2),
        },
        "monthly_trend": [
            {
                "month": m.strftime("%b %Y"),
                "interest": round(v["interest"], 2),
                "depreciation": round(v["depreciation"], 2),
            }
            for m, v in trend.items()
        ],
        "coverage_percentage": coverage_percentage,
        "coverage_numerator": recognized_count,
        "coverage_denominator": total_agreements,
    }
