import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class PostingEntryOut(BaseModel):
    period_amount: Decimal
    ytd_amount: Decimal
    posted: bool
    posted_amount: Decimal | None = None
    document_number: str | None = None
    posted_on: datetime | None = None


class PostingFilterOut(BaseModel):
    period_number: int
    period_start: date
    period_end: date
    fy_start: date
    entries: dict[str, PostingEntryOut]


class PostingRequest(BaseModel):
    agreement_id: uuid.UUID
    vendor_id: uuid.UUID
    period_number: int
    posting_type: str | None = None  # required for /post, unused for /post-interest-depreciation
