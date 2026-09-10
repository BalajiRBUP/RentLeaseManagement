import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models.agreement import AgreementStatus, PaymentFrequency
from app.schemas.masters import VendorOut, CostCenterOut, ProfitCenterOut


# ---------- Allocation ----------

class AllocationCreate(BaseModel):
    vendor_id: uuid.UUID
    cost_center_id: uuid.UUID
    profit_center_id: uuid.UUID
    split_percentage: Decimal

    @field_validator("split_percentage")
    @classmethod
    def positive_split(cls, v: Decimal) -> Decimal:
        if v <= 0 or v > 100:
            raise ValueError("split_percentage must be between 0 and 100")
        return v


class AllocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    split_percentage: Decimal
    vendor: VendorOut
    cost_center: CostCenterOut
    profit_center: ProfitCenterOut

    # Calculated fields, filled in by the CRUD layer (not stored in DB)
    calculated_rent: Decimal | None = None
    calculated_gst: Decimal | None = None
    calculated_tds: Decimal | None = None
    net_payable: Decimal | None = None


# ---------- Agreement ----------

class AgreementCreate(BaseModel):
    agreement_name: str | None = None
    property_id: uuid.UUID
    start_date: date
    end_date: date
    total_rent: Decimal
    gst_percentage: Decimal = Decimal("0")
    tds_percentage: Decimal = Decimal("0")
    payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    escalation_percentage: Decimal = Decimal("0")
    escalation_period: int = 0
    discount_rate: Decimal = Decimal("0")
    security_deposit: Decimal = Decimal("0")
    created_by: str
    allocations: list[AllocationCreate]

    @model_validator(mode="after")
    def validate_dates_and_splits(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        total_split = sum(a.split_percentage for a in self.allocations)
        if abs(total_split - Decimal("100")) > Decimal("0.01"):
            raise ValueError(f"allocation split_percentage must total 100, got {total_split}")
        return self


class AgreementUpdate(BaseModel):
    agreement_name: str | None = None
    end_date: date | None = None
    total_rent: Decimal | None = None
    gst_percentage: Decimal | None = None
    tds_percentage: Decimal | None = None
    escalation_percentage: Decimal | None = None
    escalation_period: int | None = None
    discount_rate: Decimal | None = None
    security_deposit: Decimal | None = None
    status: AgreementStatus | None = None
    modified_by: str


class AgreementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    urn: str
    agreement_name: str | None
    property_id: uuid.UUID
    start_date: date
    end_date: date
    total_rent: Decimal
    gst_percentage: Decimal
    tds_percentage: Decimal
    payment_frequency: PaymentFrequency
    escalation_percentage: Decimal
    escalation_period: int
    discount_rate: Decimal
    security_deposit: Decimal
    status: AgreementStatus
    created_by: str | None
    created_on: datetime
    modified_by: str | None
    modified_on: datetime
    allocations: list[AllocationOut] = []


class AgreementListItem(BaseModel):
    """Lighter payload for list/grid screens."""
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    urn: str
    agreement_name: str | None
    total_rent: Decimal
    status: AgreementStatus
    start_date: date
    end_date: date
