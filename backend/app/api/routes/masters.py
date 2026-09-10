import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.masters import (
    PropertyOut, PropertyCreate,
    VendorOut, VendorCreate,
    CostCenterOut, CostCenterCreate,
    ProfitCenterOut, ProfitCenterCreate,
)
from app.crud import masters as crud_masters

router = APIRouter(prefix="/api/masters", tags=["Masters"])


# ---------- Properties ----------

@router.get("/properties", response_model=list[PropertyOut])
def get_properties(db: Session = Depends(get_db)):
    return crud_masters.list_properties(db)


@router.post("/properties", response_model=PropertyOut, status_code=201)
def add_property(payload: PropertyCreate, db: Session = Depends(get_db)):
    try:
        return crud_masters.create_property(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/properties/{property_id}", response_model=PropertyOut)
def remove_property(property_id: uuid.UUID, db: Session = Depends(get_db)):
    obj = crud_masters.deactivate_property(db, property_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Property not found")
    return obj


# ---------- Vendors ----------

@router.get("/vendors", response_model=list[VendorOut])
def get_vendors(db: Session = Depends(get_db)):
    return crud_masters.list_vendors(db)


@router.post("/vendors", response_model=VendorOut, status_code=201)
def add_vendor(payload: VendorCreate, db: Session = Depends(get_db)):
    try:
        return crud_masters.create_vendor(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/vendors/{vendor_id}", response_model=VendorOut)
def remove_vendor(vendor_id: uuid.UUID, db: Session = Depends(get_db)):
    obj = crud_masters.deactivate_vendor(db, vendor_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return obj


# ---------- Cost Centers ----------

@router.get("/cost-centers", response_model=list[CostCenterOut])
def get_cost_centers(db: Session = Depends(get_db)):
    return crud_masters.list_cost_centers(db)


@router.post("/cost-centers", response_model=CostCenterOut, status_code=201)
def add_cost_center(payload: CostCenterCreate, db: Session = Depends(get_db)):
    try:
        return crud_masters.create_cost_center(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/cost-centers/{cost_center_id}", response_model=CostCenterOut)
def remove_cost_center(cost_center_id: uuid.UUID, db: Session = Depends(get_db)):
    obj = crud_masters.deactivate_cost_center(db, cost_center_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Cost center not found")
    return obj


# ---------- Profit Centers ----------

@router.get("/profit-centers", response_model=list[ProfitCenterOut])
def get_profit_centers(db: Session = Depends(get_db)):
    return crud_masters.list_profit_centers(db)


@router.post("/profit-centers", response_model=ProfitCenterOut, status_code=201)
def add_profit_center(payload: ProfitCenterCreate, db: Session = Depends(get_db)):
    try:
        return crud_masters.create_profit_center(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/profit-centers/{profit_center_id}", response_model=ProfitCenterOut)
def remove_profit_center(profit_center_id: uuid.UUID, db: Session = Depends(get_db)):
    obj = crud_masters.deactivate_profit_center(db, profit_center_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Profit center not found")
    return obj
