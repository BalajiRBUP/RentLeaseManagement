"""
Placeholder models for the next build phases (Lease Engine, Amendment Engine,
Posting). Kept here, deliberately minimal, so the overall architecture and
table relationships are visible now. Flesh these out sprint by sprint the
same way Agreement was built - don't fill them in speculatively.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Date, DateTime, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class LeaseSchedule(Base):
    """One row per period (usually monthly) of the IND AS 116 lease schedule
    generated for an agreement: ROU depreciation, interest, liability roll-forward."""
    __tablename__ = "lease_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id"), nullable=False)

    period_number = Column(Integer, nullable=False)  # 1, 2, 3... in order, for display/sorting
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    opening_liability = Column(Numeric(15, 2))
    interest_expense = Column(Numeric(15, 2))
    lease_payment = Column(Numeric(15, 2))
    closing_liability = Column(Numeric(15, 2))

    opening_rou = Column(Numeric(15, 2))
    depreciation = Column(Numeric(15, 2))
    closing_rou = Column(Numeric(15, 2))

    status = Column(String(30), default="Draft")  # Draft, Posted
    posted_on = Column(DateTime, nullable=True)
    created_on = Column(DateTime, default=datetime.utcnow)


class Amendment(Base):
    """Records a change event against an agreement: rent increase/reduction,
    end date change, discount rate change, escalation change, termination, etc."""
    __tablename__ = "amendments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id"), nullable=False)

    amendment_type = Column(String(50), nullable=False)
    # Rent Increase, Rent Reduction, End Date Change, Discounting Rate Change,
    # Escalation Percentage Change, Escalation Period Change, Partial Termination,
    # Full Termination

    effective_date = Column(Date, nullable=False)
    old_value = Column(String(255))
    new_value = Column(String(255))

    status = Column(String(30), default="Pending")  # Pending, Approved, Rejected
    requested_by = Column(String(100))
    approved_by = Column(String(100))
    approved_on = Column(DateTime, nullable=True)
    created_on = Column(DateTime, default=datetime.utcnow)

    # Filled in when the amendment is approved - the remeasurement amount
    # that Finance needs to post to SAP (liability/ROU adjustment for a
    # normal amendment, or the write-off amount for a Full Termination).
    posting_amount = Column(Numeric(15, 2), nullable=True)
    posting_status = Column(String(30), default="Not Posted")  # Not Posted, Posted
    posted_on = Column(DateTime, nullable=True)


class Posting(Base):
    """Per-vendor, per-month posting ledger for Interest/Depreciation/Rent -
    matches the AS116 script's post_interest_entry / post_depreciation_entry
    / post_recognition_entry pattern: each type posts independently, and
    Interest/Depreciation amounts are the YTD (April-to-selected-month)
    cumulative figure, not just that single month's amount."""
    __tablename__ = "postings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    period_number = Column(Integer, nullable=False)  # the lease_schedules.period_number this covers

    posting_type = Column(String(30))  # Interest, Depreciation, Rent
    document_number = Column(String(50))  # simulated JE reference, since there's no real SAP call
    amount = Column(Numeric(15, 2))  # the YTD cumulative amount as of period_number, for this vendor's split
    status = Column(String(30), default="Posted")
    posted_on = Column(DateTime, default=datetime.utcnow)
    created_on = Column(DateTime, default=datetime.utcnow)
