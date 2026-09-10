"""
Applies an approved amendment's change to its Agreement.

Two-phase flow (matches the design already agreed):
  1. Request  - user picks a type + new value + effective date -> stored as Pending,
                old_value snapshotted from the agreement at request time.
  2. Approve  - Finance approves -> this module actually mutates the Agreement,
                then the lease schedule gets regenerated.

On approval, schedule periods before the effective date remain unchanged and
only Draft periods from the effective date forward are recalculated.
"""
from decimal import Decimal, InvalidOperation
from datetime import date

from app.models.agreement import Agreement, AgreementStatus

AMENDMENT_TYPES = [
    "Rent Increase",
    "Rent Reduction",
    "End Date Change",
    "Discounting Rate Change",
    "Escalation Percentage Change",
    "Escalation Period Change",
    "Partial Termination",
    "Full Termination",
]


class AmendmentError(ValueError):
    pass


def snapshot_old_value(agreement: Agreement, amendment_type: str) -> str:
    """What the field looked like on the agreement at request time."""
    if amendment_type in ("Rent Increase", "Rent Reduction", "Partial Termination"):
        return str(agreement.total_rent)
    if amendment_type == "End Date Change":
        return str(agreement.end_date)
    if amendment_type == "Discounting Rate Change":
        return str(agreement.discount_rate)
    if amendment_type == "Escalation Percentage Change":
        return str(agreement.escalation_percentage)
    if amendment_type == "Escalation Period Change":
        return str(agreement.escalation_period)
    if amendment_type == "Full Termination":
        return str(agreement.end_date)
    raise AmendmentError(f"Unknown amendment_type: {amendment_type}")


def apply_amendment(agreement: Agreement, amendment_type: str, new_value: str, effective_date: date) -> None:
    """Mutates `agreement` in place according to the amendment type. Raises
    AmendmentError on bad input (caller should reject the amendment, not 500)."""

    if amendment_type == "Rent Increase":
        agreement.total_rent = _to_decimal(new_value)

    elif amendment_type == "Rent Reduction":
        agreement.total_rent = _to_decimal(new_value)

    elif amendment_type == "End Date Change":
        new_end_date = _to_date(new_value)
        if new_end_date < effective_date:
            raise AmendmentError("End date change cannot be earlier than its effective date")
        agreement.end_date = new_end_date

    elif amendment_type == "Discounting Rate Change":
        agreement.discount_rate = _to_decimal(new_value)

    elif amendment_type == "Escalation Percentage Change":
        agreement.escalation_percentage = _to_decimal(new_value)

    elif amendment_type == "Escalation Period Change":
        agreement.escalation_period = int(new_value)

    elif amendment_type == "Partial Termination":
        # new_value = remaining rent after partially giving back space
        agreement.total_rent = _to_decimal(new_value)
        agreement.end_date = effective_date

    elif amendment_type == "Full Termination":
        agreement.end_date = effective_date
        agreement.status = AgreementStatus.TERMINATED

    else:
        raise AmendmentError(f"Unknown amendment_type: {amendment_type}")


def _to_decimal(value: str) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        raise AmendmentError(f"'{value}' is not a valid number")


def _to_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise AmendmentError(f"'{value}' is not a valid date (expected YYYY-MM-DD)")
