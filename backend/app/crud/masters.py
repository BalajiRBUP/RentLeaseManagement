import uuid
from sqlalchemy.orm import Session

from app.models.masters import Property, Vendor, CostCenter, ProfitCenter
from app.schemas.masters import PropertyCreate, VendorCreate, CostCenterCreate, ProfitCenterCreate


# ---------- Property ----------

def list_properties(db: Session):
    return db.query(Property).filter(Property.is_active == True).all()  # noqa: E712


def create_property(db: Session, payload: PropertyCreate) -> Property:
    existing = db.query(Property).filter(Property.property_code == payload.property_code).first()
    if existing:
        raise ValueError(f"Property code '{payload.property_code}' already exists")
    obj = Property(id=uuid.uuid4(), **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def deactivate_property(db: Session, property_id: uuid.UUID) -> Property | None:
    obj = db.query(Property).filter(Property.id == property_id).first()
    if not obj:
        return None
    obj.is_active = False
    db.commit()
    return obj


# ---------- Vendor ----------

def list_vendors(db: Session):
    return db.query(Vendor).filter(Vendor.is_active == True).all()  # noqa: E712


def create_vendor(db: Session, payload: VendorCreate) -> Vendor:
    existing = db.query(Vendor).filter(Vendor.vendor_code == payload.vendor_code).first()
    if existing:
        raise ValueError(f"Vendor code '{payload.vendor_code}' already exists")
    obj = Vendor(id=uuid.uuid4(), **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def deactivate_vendor(db: Session, vendor_id: uuid.UUID) -> Vendor | None:
    obj = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not obj:
        return None
    obj.is_active = False
    db.commit()
    return obj


# ---------- Cost Center ----------

def list_cost_centers(db: Session):
    return db.query(CostCenter).filter(CostCenter.is_active == True).all()  # noqa: E712


def create_cost_center(db: Session, payload: CostCenterCreate) -> CostCenter:
    existing = db.query(CostCenter).filter(CostCenter.cost_center_code == payload.cost_center_code).first()
    if existing:
        raise ValueError(f"Cost center code '{payload.cost_center_code}' already exists")
    obj = CostCenter(id=uuid.uuid4(), **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def deactivate_cost_center(db: Session, cost_center_id: uuid.UUID) -> CostCenter | None:
    obj = db.query(CostCenter).filter(CostCenter.id == cost_center_id).first()
    if not obj:
        return None
    obj.is_active = False
    db.commit()
    return obj


# ---------- Profit Center ----------

def list_profit_centers(db: Session):
    return db.query(ProfitCenter).filter(ProfitCenter.is_active == True).all()  # noqa: E712


def create_profit_center(db: Session, payload: ProfitCenterCreate) -> ProfitCenter:
    existing = db.query(ProfitCenter).filter(
        ProfitCenter.profit_center_code == payload.profit_center_code
    ).first()
    if existing:
        raise ValueError(f"Profit center code '{payload.profit_center_code}' already exists")
    obj = ProfitCenter(id=uuid.uuid4(), **payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def deactivate_profit_center(db: Session, profit_center_id: uuid.UUID) -> ProfitCenter | None:
    obj = db.query(ProfitCenter).filter(ProfitCenter.id == profit_center_id).first()
    if not obj:
        return None
    obj.is_active = False
    db.commit()
    return obj
