"""
Run once (and again any time you add a new model) to create/update tables
in Postgres directly from the SQLAlchemy models.

    cd backend
    python scripts/create_tables.py

For a real production workflow, replace this with Alembic migrations later -
this is the fast path to get Sprint 1 running today.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import Base, engine
from app import models  # noqa: F401  (import so all models register on Base)

if __name__ == "__main__":
    print(f"Creating tables on: {engine.url}")
    Base.metadata.create_all(bind=engine)
    print("Done. Tables created:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")
