import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class LeaseSchedulePeriodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
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
    status: str
    posted_on: datetime | None = None


class LeaseScheduleSummary(BaseModel):
    agreement_id: uuid.UUID
    agreement_urn: str
    total_periods: int
    initial_liability: Decimal
    initial_rou: Decimal
    total_interest: Decimal
    total_depreciation: Decimal
    recognition_amount: Decimal | None = None
    recognition_status: str | None = None
    recognition_posted_on: datetime | None = None
    periods: list[LeaseSchedulePeriodOut]
