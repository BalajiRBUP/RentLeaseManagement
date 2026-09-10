import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    Column, String, Date, DateTime, Numeric, Integer, ForeignKey, Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class AgreementStatus(str, enum.Enum):
    DRAFT = "Draft"
    PENDING = "Pending"
    APPROVED = "Approved"
    TERMINATED = "Terminated"


class PaymentFrequency(str, enum.Enum):
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    HALF_YEARLY = "Half-Yearly"
    ANNUALLY = "Annually"


class Agreement(Base):
    __tablename__ = "agreements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    urn = Column(String(50), unique=True, nullable=False)  # system generated, e.g. AGR-000001
    agreement_name = Column(String(255))

    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    total_rent = Column(Numeric(15, 2), nullable=False)
    gst_percentage = Column(Numeric(5, 2), default=0)
    tds_percentage = Column(Numeric(5, 2), default=0)

    payment_frequency = Column(Enum(PaymentFrequency), default=PaymentFrequency.MONTHLY)

    escalation_percentage = Column(Numeric(5, 2), default=0)
    escalation_period = Column(Integer, default=0)  # months
    discount_rate = Column(Numeric(5, 2), default=0)  # IND AS 116 discounting rate
    security_deposit = Column(Numeric(15, 2), default=0)

    status = Column(Enum(AgreementStatus), default=AgreementStatus.DRAFT, nullable=False)

    created_by = Column(String(100))
    created_on = Column(DateTime, default=datetime.utcnow)
    modified_by = Column(String(100))
    modified_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Initial Recognition entry (Dr ROU Asset / Cr Lease Liability) - a
    # ONE-TIME posting made right when the schedule is first generated, not
    # per period. Set automatically whenever generate_schedule_for_agreement
    # runs; NOT touched by an amendment rebuild (that uses Amendment.posting_amount
    # instead, since it's a remeasurement, not a fresh recognition).
    recognition_amount = Column(Numeric(15, 2), nullable=True)
    recognition_status = Column(String(30), default="Not Posted")  # Not Posted, Posted
    recognition_posted_on = Column(DateTime, nullable=True)

    property = relationship("Property")
    allocations = relationship(
        "AgreementAllocation", back_populates="agreement", cascade="all, delete-orphan"
    )


class AgreementAllocation(Base):
    """
    Vendor/cost-center/profit-center split for an agreement.
    Rent, GST and TDS amounts are NEVER stored here - they are always
    calculated on the fly from Agreement.total_rent x split_percentage.
    This keeps amendments simple: change the agreement rent, and every
    allocation recalculates automatically without touching this table.
    """
    __tablename__ = "agreement_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agreement_id = Column(UUID(as_uuid=True), ForeignKey("agreements.id"), nullable=False)

    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("cost_centers.id"), nullable=False)
    profit_center_id = Column(UUID(as_uuid=True), ForeignKey("profit_centers.id"), nullable=False)

    split_percentage = Column(Numeric(5, 2), nullable=False)  # all allocations must total 100

    agreement = relationship("Agreement", back_populates="allocations")
    vendor = relationship("Vendor")
    cost_center = relationship("CostCenter")
    profit_center = relationship("ProfitCenter")
