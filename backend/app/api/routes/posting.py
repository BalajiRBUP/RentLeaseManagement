import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.posting import PostingFilterOut, PostingRequest
from app.crud import posting as crud_posting

router = APIRouter(prefix="/api/postings", tags=["Postings"])


@router.get("/filter", response_model=PostingFilterOut)
def get_filter(agreement_id: uuid.UUID, period_number: int, vendor_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        return crud_posting.get_filter_data(db, agreement_id, period_number, vendor_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/post")
def post(payload: PostingRequest, db: Session = Depends(get_db)):
    try:
        posting = crud_posting.post_entry(
            db, payload.agreement_id, payload.vendor_id, payload.period_number, payload.posting_type
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "id": posting.id,
        "posting_type": posting.posting_type,
        "amount": posting.amount,
        "document_number": posting.document_number,
        "status": posting.status,
        "posted_on": posting.posted_on,
    }


@router.post("/post-interest-depreciation")
def post_interest_depreciation(payload: PostingRequest, db: Session = Depends(get_db)):
    """One click posts both Interest and Depreciation for this vendor/month,
    each getting its own document number."""
    try:
        postings = crud_posting.post_interest_and_depreciation(
            db, payload.agreement_id, payload.vendor_id, payload.period_number
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return [
        {
            "id": p.id,
            "posting_type": p.posting_type,
            "amount": p.amount,
            "document_number": p.document_number,
            "status": p.status,
            "posted_on": p.posted_on,
        }
        for p in postings
    ]
