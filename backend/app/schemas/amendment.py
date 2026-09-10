import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.amendment_engine import AMENDMENT_TYPES


class AmendmentCreate(BaseModel):
    agreement_id: uuid.UUID
    amendment_type: str
    effective_date: date
    new_value: str
    requested_by: str

    @field_validator("amendment_type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        if v not in AMENDMENT_TYPES:
            raise ValueError(f"amendment_type must be one of: {', '.join(AMENDMENT_TYPES)}")
        return v


class AmendmentDecision(BaseModel):
    decided_by: str
    approve: bool  # True = Approve (applies the change), False = Reject


class AmendmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    agreement_id: uuid.UUID
    amendment_type: str
    effective_date: date
    old_value: str | None
    new_value: str | None
    status: str
    requested_by: str | None
    approved_by: str | None
    approved_on: datetime | None
    created_on: datetime
    posting_amount: Decimal | None = None
    posting_status: str | None = None
    posted_on: datetime | None = None
