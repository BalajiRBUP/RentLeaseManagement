"""
Populate master tables with a handful of sample rows so you can create your
first Agreement end-to-end through the React app.

    cd backend
    python scripts/seed_data.py

Safe to re-run - it skips rows that already exist (matched by code).
"""
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal
from app.models.masters import Property, Vendor, CostCenter, ProfitCenter

PROPERTIES = [
    ("PROP-001", "Chennai Regional Office", "Chennai"),
    ("PROP-002", "GMMCO Warehouse - Perungudi", "Chennai"),
]

VENDORS = [
    ("V-1001", "ABC Properties Pvt Ltd"),
    ("V-1002", "XYZ Estates LLP"),
]

COST_CENTERS = [
    ("CC-100", "Sales & Marketing"),
    ("CC-200", "Operations"),
]

PROFIT_CENTERS = [
    ("PC-100", "Chennai Region"),
    ("PC-200", "Corporate"),
]


def seed():
    db = SessionLocal()
    try:
        for code, name, location in PROPERTIES:
            if not db.query(Property).filter_by(property_code=code).first():
                db.add(Property(id=uuid.uuid4(), property_code=code, property_name=name, location=location))

        for code, name in VENDORS:
            if not db.query(Vendor).filter_by(vendor_code=code).first():
                db.add(Vendor(id=uuid.uuid4(), vendor_code=code, vendor_name=name))

        for code, text in COST_CENTERS:
            if not db.query(CostCenter).filter_by(cost_center_code=code).first():
                db.add(CostCenter(id=uuid.uuid4(), cost_center_code=code, cost_center_text=text))

        for code, text in PROFIT_CENTERS:
            if not db.query(ProfitCenter).filter_by(profit_center_code=code).first():
                db.add(ProfitCenter(id=uuid.uuid4(), profit_center_code=code, profit_center_text=text))

        db.commit()
        print("Seed data inserted (or already present).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
