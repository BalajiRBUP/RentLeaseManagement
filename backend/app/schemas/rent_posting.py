import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RentPostingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    agreement_id: uuid.UUID
    vendor_id: uuid.UUID
    period_number: int
    calculated_rent_amount: Decimal
    invoice_amount: Decimal
    invoice_file_name: str
    status: str
    submitted_by: str | None
    submitted_on: datetime
    approved_by: str | None
    approved_on: datetime | None

    # enriched for display - filled in by the route, not stored redundantly
    agreement_urn: str | None = None
    agreement_name: str | None = None
    property_name: str | None = None
    vendor_name: str | None = None
    all_vendors_on_agreement: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    document_number: str | None = None
    posted_amount: Decimal | None = None


class BulkDecisionRequest(BaseModel):
    request_ids: list[uuid.UUID]
    decided_by: str
    approve: bool
