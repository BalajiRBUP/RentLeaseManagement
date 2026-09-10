import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.rent_posting import RentPostingOut, BulkDecisionRequest
from app.crud import rent_posting as crud_rent_posting

router = APIRouter(prefix="/api/rent-postings", tags=["Rent Postings"])


@router.get("/rent-cap")
def get_rent_cap(agreement_id: uuid.UUID, vendor_id: uuid.UUID, period_number: int, db: Session = Depends(get_db)):
    """So the Operational SPOC's form can show the max allowed amount
    before they even submit."""
    try:
        cap = crud_rent_posting.get_rent_cap(db, agreement_id, vendor_id, period_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"calculated_rent_amount": cap}


@router.post("", response_model=RentPostingOut, status_code=201)
async def submit_invoice(
    agreement_id: uuid.UUID = Form(...),
    vendor_id: uuid.UUID = Form(...),
    period_number: int = Form(...),
    invoice_amount: float = Form(...),
    submitted_by: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    file_bytes = await file.read()
    try:
        submission = crud_rent_posting.create_submission(
            db, agreement_id, vendor_id, period_number, invoice_amount, submitted_by, file_bytes, file.filename
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return submission


@router.get("/pending", response_model=list[RentPostingOut])
def get_pending(db: Session = Depends(get_db)):
    return crud_rent_posting.list_pending(db)


@router.get("/history", response_model=list[RentPostingOut])
def get_history(
    agreement_id: uuid.UUID | None = None,
    month: str | None = None,
    db: Session = Depends(get_db),
):
    return crud_rent_posting.list_history(db, agreement_id=agreement_id, month=month)


@router.get("/agreement/{agreement_id}", response_model=list[RentPostingOut])
def get_for_agreement(agreement_id: uuid.UUID, db: Session = Depends(get_db)):
    """Full rent payment picture for one agreement's detail page - every
    invoice regardless of status (Submitted/Approved/Rejected)."""
    return crud_rent_posting.list_for_agreement(db, agreement_id)


@router.post("/bulk-decision")
def bulk_decision(payload: BulkDecisionRequest, db: Session = Depends(get_db)):
    return crud_rent_posting.bulk_decide(db, payload.request_ids, payload.decided_by, payload.approve)


@router.get("/{request_id}/download")
def download_attachment(request_id: uuid.UUID, db: Session = Depends(get_db)):
    submission = crud_rent_posting.get_for_download(db, request_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return FileResponse(
        path=submission.invoice_file_path,
        filename=submission.invoice_file_name,
        media_type="application/octet-stream",
    )
