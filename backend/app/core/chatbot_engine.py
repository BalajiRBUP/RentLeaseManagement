"""
AI chat assistant that answers questions about the Rent & Lease data using
the app's own PostgreSQL database as its knowledge base - no external API,
no data leaving the machine. Talks to a locally running Ollama model.

Flow for every question:
  1. Send the question + a hand-written description of the schema to the
     local LLM, asking it to reply with ONE read-only SQL SELECT statement.
  2. Validate that SQL extremely strictly (SELECT-only, single statement,
     known tables only, forced LIMIT) before it ever touches the database.
  3. Run it against the real DB with SQLAlchemy.
  4. Send the question + the resulting rows back to the same local LLM and
     ask it to summarize the answer in plain English.

Requires Ollama (https://ollama.com) running locally with a model pulled,
e.g.:   ollama pull llama3.1:8b
"""
import json
import re

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings

# ---------------------------------------------------------------------------
# Schema knowledge base
# ---------------------------------------------------------------------------
# Hand-written rather than auto-introspected: this gives the LLM the
# *meaning* of each table/column (not just names), which matters far more
# than raw DDL for getting correct SQL out of a small local model.
SCHEMA_CONTEXT = """
You are working with a PostgreSQL database for a Rent & Lease Management
system (IND AS 116 lease accounting). Tables:

properties(id uuid, property_code text, property_name text, location text, is_active bool)
vendors(id uuid, vendor_code text, vendor_name text, is_active bool)
cost_centers(id uuid, cost_center_code text, cost_center_text text, is_active bool)
profit_centers(id uuid, profit_center_code text, profit_center_text text, is_active bool)

agreements(
  id uuid, urn text,               -- system id like AGR-000001
  agreement_name text,
  property_id uuid -> properties.id,
  start_date date, end_date date,
  total_rent numeric, gst_percentage numeric, tds_percentage numeric,
  payment_frequency text,          -- Monthly / Quarterly / Half-Yearly / Annually
  escalation_percentage numeric, escalation_period integer,
  discount_rate numeric, security_deposit numeric,
  status text,                     -- Draft / Pending / Approved / Terminated
  recognition_amount numeric, recognition_status text  -- Not Posted / Posted
)

agreement_allocations(
  id uuid, agreement_id uuid -> agreements.id,
  vendor_id uuid -> vendors.id, cost_center_id uuid -> cost_centers.id,
  profit_center_id uuid -> profit_centers.id,
  split_percentage numeric          -- rent/GST/TDS are NOT stored here, they are
                                     -- always agreement.total_rent * split_percentage
)

lease_schedules(
  id uuid, agreement_id uuid -> agreements.id,
  period_number integer, period_start date, period_end date,
  opening_liability numeric, interest_expense numeric,
  lease_payment numeric, closing_liability numeric,
  opening_rou numeric, depreciation numeric, closing_rou numeric,
  status text                       -- Draft / Posted
)

amendments(
  id uuid, agreement_id uuid -> agreements.id,
  amendment_type text,              -- Rent Increase, Rent Reduction, End Date Change,
                                     -- Discounting Rate Change, Escalation Percentage Change,
                                     -- Escalation Period Change, Partial Termination, Full Termination
  effective_date date, old_value text, new_value text,
  status text,                      -- Pending / Approved / Rejected
  posting_amount numeric, posting_status text
)

postings(
  id uuid, agreement_id uuid -> agreements.id, vendor_id uuid -> vendors.id,
  period_number integer,
  posting_type text,                -- Interest / Depreciation / Rent
  document_number text, amount numeric, status text
)

rent_postings(
  id uuid, agreement_id uuid -> agreements.id, vendor_id uuid -> vendors.id,
  period_number integer,
  calculated_rent_amount numeric, invoice_amount numeric,
  status text,                      -- Submitted / Approved / Rejected
  submitted_on timestamp, approved_on timestamp
)

Notes:
- Money columns are numeric; cast to numeric/float when doing math.
- "current" or "outstanding" liability/ROU means the closing_liability /
  closing_rou of the most recent lease_schedules row where period_end < today.
- Always join to properties/vendors/agreements to show human-readable names,
  not just ids, unless the question explicitly asks for ids.
"""

ALLOWED_TABLES = {
    "properties", "vendors", "cost_centers", "profit_centers",
    "agreements", "agreement_allocations", "lease_schedules",
    "amendments", "postings", "rent_postings",
}

# Anything containing these (case-insensitive, word-boundary) anywhere in the
# generated SQL causes an immediate hard rejection - no attempt is made to
# "fix" or sanitize the query, it is just refused.
FORBIDDEN_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter", "truncate", "grant",
    "revoke", "create", "replace", "merge", "call", "execute", "copy",
    "vacuum", "reindex", "comment", "into outfile", "--", "/*", ";",
]

MAX_ROWS = 50


class ChatbotError(Exception):
    """Raised for any expected/user-facing failure (Ollama down, bad SQL, etc.)."""


def _call_ollama(prompt: str, system: str | None = None) -> str:
    try:
        resp = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "options": {"temperature": 0.1},
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except httpx.ConnectError as exc:
        raise ChatbotError(
            "Can't reach the local AI model. Make sure Ollama is running "
            f"(ollama serve) and that '{settings.OLLAMA_MODEL}' has been "
            "pulled (ollama pull " + settings.OLLAMA_MODEL + ")."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise ChatbotError(f"Local AI model returned an error: {exc}") from exc


def _extract_sql(raw: str) -> str:
    """Pull the SELECT statement out of the model's reply, stripping any
    ```sql fences, prose, or explanation the model added despite instructions."""
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    candidate = fenced.group(1) if fenced else raw
    match = re.search(r"select\b.*", candidate, re.DOTALL | re.IGNORECASE)
    if not match:
        raise ChatbotError("Couldn't turn that into a database query. Try rephrasing it.")
    sql = match.group(0).strip().rstrip(";").strip()
    return sql


def _validate_sql(sql: str) -> str:
    lowered = sql.lower()

    if not lowered.lstrip().startswith("select"):
        raise ChatbotError("Only read-only questions are supported (no changes to data).")

    for kw in FORBIDDEN_KEYWORDS:
        if kw in lowered:
            raise ChatbotError("That question would require a write/unsafe operation, which isn't allowed.")

    tables_referenced = set(re.findall(r"(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", lowered))
    unknown = tables_referenced - ALLOWED_TABLES
    if unknown:
        raise ChatbotError(f"That query references unknown table(s): {', '.join(unknown)}.")

    if "limit" not in lowered:
        sql = f"{sql}\nLIMIT {MAX_ROWS}"

    return sql


def _rows_to_dicts(result) -> tuple[list[str], list[dict]]:
    columns = list(result.keys())
    rows = []
    for row in result.fetchmany(MAX_ROWS):
        d = {}
        for col, val in zip(columns, row):
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            elif hasattr(val, "__float__") and not isinstance(val, (int, float, bool)):
                val = float(val)
            d[col] = val
        rows.append(d)
    return columns, rows


def ask_question(question: str, db: Session) -> dict:
    if not question or not question.strip():
        raise ChatbotError("Please type a question.")

    sql_prompt = (
        f"{SCHEMA_CONTEXT}\n\n"
        f"Write ONE read-only PostgreSQL SELECT query that answers this question. "
        f"Reply with ONLY the SQL, no explanation, no markdown.\n\n"
        f"Question: {question}\n\nSQL:"
    )
    raw_sql_reply = _call_ollama(
        sql_prompt,
        system="You are a precise SQL generator. Output only a single SELECT statement.",
    )
    sql = _extract_sql(raw_sql_reply)
    sql = _validate_sql(sql)

    try:
        result = db.execute(text(sql))
        columns, rows = _rows_to_dicts(result)
    except Exception as exc:
        raise ChatbotError(f"The query didn't run cleanly against the database ({exc}).") from exc

    # Fast path: a single-row, single-column result is almost always a plain
    # COUNT/SUM/AVG aggregate. Format it directly instead of making a second,
    # slow round-trip to the local model just to restate one number.
    if len(rows) == 1 and len(columns) == 1:
        value = rows[0][columns[0]]
        label = columns[0].replace("_", " ")
        return {
            "answer": f"{label.capitalize()}: {value}",
            "sql": sql,
            "columns": columns,
            "rows": rows,
        }

    if not rows:
        return {
            "answer": "No matching records found.",
            "sql": sql,
            "columns": columns,
            "rows": rows,
        }

    summary_prompt = (
        f"Question: {question}\n\n"
        f"Query result (JSON, up to {MAX_ROWS} rows): {json.dumps(rows, default=str)}\n\n"
        "Answer the question in 1-4 concise sentences of plain English using only "
        "this data. Mention actual figures/names where relevant. If the result "
        "is empty, say so plainly rather than guessing."
    )
    answer = _call_ollama(
        summary_prompt,
        system="You are a helpful assistant summarizing database results for a business user. Be concise and accurate.",
    )

    return {"answer": answer, "sql": sql, "columns": columns, "rows": rows}