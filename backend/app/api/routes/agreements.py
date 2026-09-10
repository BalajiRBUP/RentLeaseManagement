import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.database import get_db
from app.schemas.agreement import AgreementCreate, AgreementUpdate, AgreementOut, AgreementListItem
from app.crud import agreement as crud_agreement

router = APIRouter(prefix="/api/agreements", tags=["Agreements"])


@router.post("", response_model=AgreementOut, status_code=201)
def create_agreement(payload: AgreementCreate, db: Session = Depends(get_db)):
    agreement = crud_agreement.create_agreement(db, payload)
    agreement = crud_agreement.attach_calculated_amounts(agreement)
    return agreement


@router.get("", response_model=list[AgreementListItem])
def list_agreements(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return crud_agreement.list_agreements(db, skip=skip, limit=limit)


@router.get("/export")
def export_agreements(db: Session = Depends(get_db)):
    return jsonable_encoder(crud_agreement.export_agreements_with_amendments(db))


@router.get("/{agreement_id}", response_model=AgreementOut)
def get_agreement(agreement_id: uuid.UUID, db: Session = Depends(get_db)):
    agreement = crud_agreement.get_agreement(db, agreement_id)
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    agreement = crud_agreement.attach_calculated_amounts(agreement)
    return agreement


@router.put("/{agreement_id}", response_model=AgreementOut)
def update_agreement(agreement_id: uuid.UUID, payload: AgreementUpdate, db: Session = Depends(get_db)):
    agreement = crud_agreement.update_agreement(db, agreement_id, payload)
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    agreement = crud_agreement.get_agreement(db, agreement_id)
    agreement = crud_agreement.attach_calculated_amounts(agreement)
    return agreement
