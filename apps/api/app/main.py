from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import analytics, assistant, export, health, ingestion, records

settings = get_settings()

app = FastAPI(
    title="Thai Public Procurement Intelligence API",
    version="0.1.0",
    description="Search, analytics, ingestion, and optional AI endpoints for public procurement records.",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


app.include_router(health.router, prefix="/api")
app.include_router(records.router, prefix="/api")
app.include_router(records.semantic_router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(ingestion.router, prefix="/api")
app.include_router(assistant.router, prefix="/api")
app.include_router(export.router, prefix="/api")

