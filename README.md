# Rent & Lease Management System

A unified web replacement for the two Power Apps (`Rent_Management_System` and
`Lease_Management_IND_AS_116`) — one app, one database, one login, built on
PostgreSQL + FastAPI + React, per the architecture decided in the earlier
ChatGPT planning thread (which never actually got to working code — this
does).

Status: **Agreement module is fully built, tested end-to-end, and working.**
Lease Schedule, Amendment, and Posting have DB tables scaffolded
(`app/models/future_modules.py`) ready for the next build pass, same way
Agreement was done — model → schema → CRUD → route → screen.

## Architecture

```
Postgres  <---  FastAPI (SQLAlchemy + Pydantic)  <---  React (Vite)
```

- **agreements** / **agreement_allocations** — core Sprint 1 tables. GST and
  TDS are never stored per vendor; they're always calculated from the
  agreement's `total_rent` × the vendor's `split_percentage`, so an
  amendment to the rent recalculates every allocation automatically.
- **properties / vendors / cost_centers / profit_centers** — master data
  (stand-ins for your SharePoint lists / SQL views like `vwLFA1`,
  `vwCost_Profit_Data`).
- **lease_schedules / amendments / postings** — scaffolded tables for the
  next sprints (ROU/liability/interest schedule, the six amendment types,
  and SAP OData posting log).

## Prerequisites

- PostgreSQL 14+ running locally (or reachable)
- Python 3.11+
- Node.js 18+

## 1. Database + Backend

```bash
cd backend
cp .env.example .env          # edit DATABASE_URL with your real Postgres password
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# create the database once (outside this project), e.g.:
#   psql -U postgres -c "CREATE DATABASE rent_lease_db;"

python scripts/create_tables.py     # creates all 9 tables
python scripts/seed_data.py         # inserts sample properties/vendors/cost centers

uvicorn app.main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs

## 2. Frontend

```bash
cd frontend
cp .env.example .env          # points to http://localhost:8000 by default
npm install
npm run dev
```

App: http://localhost:5173

Create an agreement, add vendor allocation rows (split % must total 100),
watch the calculated rent/GST/TDS/net payable update live, save, then view
it on the detail screen.

## Project layout

```
backend/
  app/
    config.py          # settings from .env
    database.py         # SQLAlchemy engine/session
    models/              # agreement.py (core), masters.py, future_modules.py (stubs)
    schemas/              # Pydantic request/response models + validation
    core/calculations.py  # the rent/GST/TDS split engine
    crud/                 # DB operations
    api/routes/            # FastAPI endpoints
    main.py               # app entrypoint, CORS, router wiring
  scripts/
    create_tables.py       # Base.metadata.create_all
    seed_data.py            # sample master data
frontend/
  src/
    api/client.js           # axios wrapper for every endpoint
    components/              # Sidebar, Layout
    pages/
      Dashboard.jsx
      agreements/             # List, Form (with live calc preview), Detail
```

## Next sprints (same pattern as Agreement)

1. **Lease Engine** — generate `lease_schedules` rows from an agreement
   (ROU, liability, interest, depreciation) using your existing Python
   calculation logic.
2. **Amendment Engine** — the six amendment types against an agreement,
   each recomputing the schedule from the effective date forward.
3. **Posting** — push schedule lines to SAP via OData (reuse your existing
   `rent_sap_posting.py` patterns: CSRF token handling, retries).
4. **Auth + roles** — Level 1/2 approval workflow, matching the Power App's
   Operational SPOC / Finance SPOC / Approval screens.
