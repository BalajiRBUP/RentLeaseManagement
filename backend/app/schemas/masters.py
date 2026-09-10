import uuid
from pydantic import BaseModel, ConfigDict


# ---------- Property ----------

class PropertyCreate(BaseModel):
    property_code: str
    property_name: str
    location: str | None = None


class PropertyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    property_code: str
    property_name: str
    location: str | None = None
    is_active: bool = True


# ---------- Vendor ----------

class VendorCreate(BaseModel):
    vendor_code: str
    vendor_name: str


class VendorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    vendor_code: str
    vendor_name: str
    is_active: bool = True


# ---------- Cost Center ----------

class CostCenterCreate(BaseModel):
    cost_center_code: str
    cost_center_text: str


class CostCenterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cost_center_code: str
    cost_center_text: str
    is_active: bool = True


# ---------- Profit Center ----------

class ProfitCenterCreate(BaseModel):
    profit_center_code: str
    profit_center_text: str


class ProfitCenterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    profit_center_code: str
    profit_center_text: str
    is_active: bool = True
