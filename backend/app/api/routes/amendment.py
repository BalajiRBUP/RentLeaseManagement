import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.amendment import AmendmentCreate, AmendmentDecision, AmendmentOut
from app.core.amendment_engine import AMENDMENT_TYPES, AmendmentError
from app.crud import amendment as crud_amendment

router = APIRouter(prefix="/api/amendments", tags=["Amendments"])


@router.get("/types")
def get_amendment_types():
    return AMENDMENT_TYPES


@router.post("", response_model=AmendmentOut, status_code=201)
def create_amendment(payload: AmendmentCreate, db: Session = Depends(get_db)):
    try:
        return crud_amendment.create_amendment(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/agreement/{agreement_id}", response_model=list[AmendmentOut])
def list_amendments(agreement_id: uuid.UUID, db: Session = Depends(get_db)):
    return crud_amendment.list_amendments_for_agreement(db, agreement_id)


@router.post("/{amendment_id}/decision", response_model=AmendmentOut)
def decide_amendment(amendment_id: uuid.UUID, payload: AmendmentDecision, db: Session = Depends(get_db)):
    try:
        return crud_amendment.decide_amendment(db, amendment_id, payload.decided_by, payload.approve)
    except AmendmentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{amendment_id}/post", response_model=AmendmentOut)
def post_amendment(amendment_id: uuid.UUID, db: Session = Depends(get_db)):
    """Marks the amendment's remeasurement/write-off amount as Posted to
    SAP. No external call - backend-only status flip, same as period posting."""
    try:
        return crud_amendment.mark_amendment_posted(db, amendment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
