"""
IND AS 116 lease schedule engine.

This mirrors the logic in the signed-off UAT script (As116_Final_UAT_Signed_Off_Script.txt):
  - New lease: full schedule from lease start to lease end, with first/last
    month rent pro-ration when the start/end date is mid-month.
  - Amendment: does NOT regenerate the whole schedule. It freezes everything
    before the rebuild start date, and only recalculates forward from there:
      * rebuild_start_date = the later of (amendment effective month) and
        (the month after the last posted month, if any)
      * old opening liability/ROU = the closing balances of the last frozen
        (pre-rebuild) period
      * revised PV of the remaining payments (using the new rent/discount
        rate/escalation) becomes the new opening liability
      * liability_adjustment = revised PV - old opening liability
      * new opening ROU = old opening ROU + liability_adjustment (floored at 0)
      * depreciation for the remaining periods = new opening ROU / remaining_months
      * month 1 of the rebuild blends old rent and new rent by day-count if
        the effective date is mid-month
      * last period pro-rates rent if the lease end date is mid-month, and
        forces principal/interest/depreciation to zero out exactly

Escalation counting restarts at 1 from the rebuild start date (matches the
production script's behavior - it does not track escalation cycles from the
original lease start once an amendment happens).
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from calendar import monthrange
from dateutil.relativedelta import relativedelta

TWO_DP = Decimal("0.01")


def round2(value: Decimal) -> Decimal:
    return value.quantize(TWO_DP, rounding=ROUND_HALF_UP)


@dataclass
class SchedulePeriod:
    period_number: int
    period_start: date
    period_end: date
    opening_liability: Decimal
    interest_expense: Decimal
    lease_payment: Decimal
    closing_liability: Decimal
    opening_rou: Decimal
    depreciation: Decimal
    closing_rou: Decimal


def month_start_dates(start_date: date, end_date: date) -> list[date]:
    """Month-start dates from start_date to end_date inclusive (one per period)."""
    dates = []
    current = start_date.replace(day=1)
    while current <= end_date:
        dates.append(current)
        current = current + relativedelta(months=1)
    return dates


def _discount_factor(month_no: int, monthly_rate: Decimal) -> Decimal:
    if monthly_rate == 0:
        return Decimal("1")
    factor = Decimal("1") / ((Decimal("1") + monthly_rate) ** month_no)
    return factor.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _proration_factor(d: date, mode: str) -> Decimal:
    """mode='start': remaining days / days in month (lease commencement).
    mode='end': elapsed days / days in month (lease/period termination)."""
    total_days = monthrange(d.year, d.month)[1]
    applicable_days = (total_days - d.day + 1) if mode == "start" else d.day
    return Decimal(applicable_days) / Decimal(total_days)


def _period_display_range(period_start_month: date, actual_start: date, actual_end: date, is_first: bool, is_last: bool):
    """What to show in period_start/period_end columns: the true lease start
    on row 1, the true lease end on the last row, month boundaries otherwise."""
    p_start = actual_start if is_first else period_start_month
    month_end = period_start_month + relativedelta(day=31)
    p_end = actual_end if is_last else month_end
    return p_start, p_end


# ---------------------------------------------------------------------------
# NEW LEASE - full schedule
# ---------------------------------------------------------------------------

def generate_lease_schedule(
    start_date: date,
    end_date: date,
    total_rent: Decimal,
    escalation_percentage: Decimal,
    escalation_period: int,
    discount_rate: Decimal,
) -> list[SchedulePeriod]:
    schedule_dates = month_start_dates(start_date, end_date)
    total_months = len(schedule_dates)
    monthly_rate = (discount_rate / Decimal("100")) / Decimal("12")

    # First month proration (mid-month lease start)
    if start_date.day != 1:
        first_month_proration = _proration_factor(start_date, "start")
        first_month_rent = round2(total_rent * first_month_proration)
    else:
        first_month_proration = Decimal("1")
        first_month_rent = total_rent

    # Last month proration (mid-month lease end)
    last_day_of_end_month = monthrange(end_date.year, end_date.month)[1]
    if end_date.day != last_day_of_end_month:
        last_month_proration = _proration_factor(end_date, "end")
    else:
        last_month_proration = Decimal("1")

    # ---- Pass 1: total initial PV ----
    pv_sum = Decimal("0")
    current_rent = total_rent
    for i in range(1, total_months + 1):
        if escalation_percentage > 0 and escalation_period and i > 1 and (i - 1) % escalation_period == 0:
            current_rent = current_rent * (Decimal("1") + escalation_percentage / Decimal("100"))

        rent_for_pv = first_month_rent if i == 1 else current_rent
        if i == total_months and last_month_proration != Decimal("1"):
            rent_for_pv = round2(rent_for_pv * last_month_proration)

        pv_sum += rent_for_pv * _discount_factor(i, monthly_rate)

    total_initial_pv = round2(pv_sum)

    opening_liability = total_initial_pv
    opening_rou = total_initial_pv
    depreciation_base = round2(total_initial_pv / total_months) if total_months else Decimal("0")

    # ---- Pass 2: build schedule ----
    periods: list[SchedulePeriod] = []
    current_rent = total_rent

    for i, month_start in enumerate(schedule_dates, start=1):
        if escalation_percentage > 0 and escalation_period and i > 1 and (i - 1) % escalation_period == 0:
            current_rent = round2(current_rent * (Decimal("1") + escalation_percentage / Decimal("100")))

        rent_this_month = first_month_rent if i == 1 else current_rent
        if i == total_months and last_month_proration != Decimal("1"):
            rent_this_month = round2(rent_this_month * last_month_proration)

        is_partial_first = (i == 1 and start_date.day != 1 and i != total_months)

        if is_partial_first:
            interest_expense = round2(opening_liability * monthly_rate * first_month_proration)
            depreciation = round2(depreciation_base * first_month_proration)
            payment = round2(rent_this_month - interest_expense)
        else:
            interest_expense = round2(opening_liability * monthly_rate)
            depreciation = depreciation_base
            payment = round2(rent_this_month - interest_expense)

        closing_liability = round2(opening_liability - payment)
        closing_rou = round2(opening_rou - depreciation)

        is_last = (i == total_months)
        if is_last:
            payment = opening_liability  # principal component clears exactly
            interest_expense = round2(rent_this_month - opening_liability)
            depreciation = opening_rou
            closing_liability = Decimal("0.00")
            closing_rou = Decimal("0.00")

        p_start, p_end = _period_display_range(month_start, start_date, end_date, i == 1, is_last)

        periods.append(SchedulePeriod(
            period_number=i,
            period_start=p_start,
            period_end=p_end,
            opening_liability=opening_liability,
            interest_expense=interest_expense,
            lease_payment=rent_this_month,
            closing_liability=closing_liability,
            opening_rou=opening_rou,
            depreciation=depreciation,
            closing_rou=closing_rou,
        ))

        opening_liability = closing_liability
        opening_rou = closing_rou

    return periods


# ---------------------------------------------------------------------------
# AMENDMENT - rebuild forward from the effective date only
# ---------------------------------------------------------------------------

def compute_rebuild_start(effective_date: date, last_posted_month_end: date | None) -> date:
    """The month we start rebuilding from: the later of the amendment's
    effective month and the month right after the last posted period."""
    amendment_month = effective_date.replace(day=1)
    if last_posted_month_end is None:
        return amendment_month
    next_month = (last_posted_month_end.replace(day=1) + relativedelta(months=1))
    return max(amendment_month, next_month)


def generate_amendment_rebuild(
    rebuild_start_date: date,
    lease_end_date: date,
    new_total_rent: Decimal,
    old_total_rent: Decimal,
    escalation_percentage: Decimal,
    escalation_period: int,
    discount_rate: Decimal,
    old_opening_liability: Decimal,
    old_opening_rou: Decimal,
    starting_period_number: int,
    amendment_effective_date: date,
) -> tuple[list[SchedulePeriod], Decimal]:
    """Returns (new periods from rebuild_start_date to lease_end_date, liability_adjustment)."""
    schedule_dates = month_start_dates(rebuild_start_date, lease_end_date)
    remaining_months = len(schedule_dates)
    if remaining_months <= 0:
        raise ValueError("No remaining months to rebuild - check the effective date against the lease end date")

    monthly_rate = (discount_rate / Decimal("100")) / Decimal("12")

    # Blended rent for the first rebuilt month, if the effective date lands mid-month
    rebuild_month_days = monthrange(rebuild_start_date.year, rebuild_start_date.month)[1]
    if amendment_effective_date.day != 1:
        days_old = amendment_effective_date.day - 1
        days_new = rebuild_month_days - days_old
        blended_rent = round2(
            (old_total_rent * days_old + new_total_rent * days_new) / Decimal(rebuild_month_days)
        )
    else:
        blended_rent = new_total_rent

    # Last-period proration if the (possibly amended) lease end date is mid-month
    last_day_of_end_month = monthrange(lease_end_date.year, lease_end_date.month)[1]
    if lease_end_date.day != last_day_of_end_month:
        last_month_proration = _proration_factor(lease_end_date, "end")
    else:
        last_month_proration = Decimal("1")

    # ---- Pass 1: revised PV of the remaining payments ----
    pv_sum = Decimal("0")
    current_rent = new_total_rent
    for i in range(1, remaining_months + 1):
        if escalation_percentage > 0 and escalation_period and i > 1 and (i - 1) % escalation_period == 0:
            current_rent = current_rent * (Decimal("1") + escalation_percentage / Decimal("100"))

        rent_for_pv = blended_rent if i == 1 else current_rent
        if i == remaining_months and last_month_proration != Decimal("1"):
            rent_for_pv = round2(rent_for_pv * last_month_proration)

        pv_sum += rent_for_pv * _discount_factor(i, monthly_rate)

    revised_total_pv = round2(pv_sum)
    liability_adjustment = round2(revised_total_pv - old_opening_liability)

    opening_liability = revised_total_pv
    opening_rou = round2(old_opening_rou + liability_adjustment)
    if opening_rou < 0:
        opening_rou = Decimal("0.00")

    depreciation_base = round2(opening_rou / remaining_months) if remaining_months else Decimal("0")

    # ---- Pass 2: build the rebuilt periods ----
    periods: list[SchedulePeriod] = []
    current_rent = new_total_rent

    for i, month_start in enumerate(schedule_dates, start=1):
        if escalation_percentage > 0 and escalation_period and i > 1 and (i - 1) % escalation_period == 0:
            current_rent = round2(current_rent * (Decimal("1") + escalation_percentage / Decimal("100")))

        rent_this_month = blended_rent if i == 1 else current_rent
        if i == remaining_months and last_month_proration != Decimal("1"):
            rent_this_month = round2(rent_this_month * last_month_proration)

        interest_expense = round2(opening_liability * monthly_rate)
        depreciation = depreciation_base
        payment = round2(rent_this_month - interest_expense)

        closing_liability = round2(opening_liability - payment)
        closing_rou = round2(opening_rou - depreciation)

        is_last = (i == remaining_months)
        if is_last:
            payment = opening_liability
            interest_expense = round2(rent_this_month - opening_liability)
            depreciation = opening_rou
            closing_liability = Decimal("0.00")
            closing_rou = Decimal("0.00")

        p_start, p_end = _period_display_range(month_start, rebuild_start_date, lease_end_date, i == 1, is_last)

        periods.append(SchedulePeriod(
            period_number=starting_period_number + i - 1,
            period_start=p_start,
            period_end=p_end,
            opening_liability=opening_liability,
            interest_expense=interest_expense,
            lease_payment=rent_this_month,
            closing_liability=closing_liability,
            opening_rou=opening_rou,
            depreciation=depreciation,
            closing_rou=closing_rou,
        ))

        opening_liability = closing_liability
        opening_rou = closing_rou

    return periods, liability_adjustment
