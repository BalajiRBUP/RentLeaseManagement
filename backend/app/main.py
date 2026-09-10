from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import agreements, masters, dashboard, lease_schedule, amendment, posting, rent_posting, chatbot

app = FastAPI(
    title="Rent & Lease Management System API",
    description="Backend for the unified Rent + IND AS 116 Lease Management system.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agreements.router)
app.include_router(masters.router)
app.include_router(dashboard.router)
app.include_router(lease_schedule.router)
app.include_router(amendment.router)
app.include_router(posting.router)
app.include_router(rent_posting.router)
app.include_router(chatbot.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
