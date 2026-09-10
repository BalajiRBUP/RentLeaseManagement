import uuid
from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_code = Column(String(50), unique=True, nullable=False)
    property_name = Column(String(255), nullable=False)
    location = Column(String(255))
    is_active = Column(Boolean, default=True)


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_code = Column(String(50), unique=True, nullable=False)  # maps to SAP LFA1
    vendor_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)


class CostCenter(Base):
    __tablename__ = "cost_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cost_center_code = Column(String(50), unique=True, nullable=False)
    cost_center_text = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)


class ProfitCenter(Base):
    __tablename__ = "profit_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profit_center_code = Column(String(50), unique=True, nullable=False)
    profit_center_text = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
