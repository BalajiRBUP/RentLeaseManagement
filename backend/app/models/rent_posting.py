import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class RentPosting(Base):
    """
    Operational SPOC submits one invoice per vendor per month (attachment +
    invoice amount, capped at that vendor's calculated rent for the month).
    Finance SPOC then bulk-approves (or rejects) - approving marks it Posted.

    This is separate from the AS116 Interest/Depreciation/Rent postings in
    app/crud/posting.py - those are the accounting JE side; this is the
    actual vendor invoice / payment approval workflow.
    """
    __tablename__ = "rent_postings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    period_number = Column(Integer, nullable=False)  # the lease_schedules.period_number (month) this covers

    calculated_rent_amount = Column(Numeric(15, 2), nullable=False)  # cap, snapshotted at submission time
    invoice_amount = Column(Numeric(15, 2), nullable=False)

    invoice_file_name = Column(String(255), nullable=False)  # original filename, shown to Finance
    invoice_file_path = Column(String(500), nullable=False)  # where it's actually stored on disk

    status = Column(String(30), default="Submitted")  # Submitted, Approved, Rejected
    submitted_by = Column(String(100))
    submitted_on = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(String(100))
    approved_on = Column(DateTime, nullable=True)
