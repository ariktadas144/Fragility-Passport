"""FastAPI application entrypoint. Wires together every router, enables
CORS for the frontend, creates database tables on startup, and runs the
alert auto-escalation timer as a background task for as long as the app is
running. Start with: uvicorn app.main:app --reload (from backend/)."""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import (
    accelerometer,
    alerts,
    assistant,
    dashboard,
    events,
    health,
    passports,
    products,
    reports,
    videos,
)
from app.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.database import SessionLocal, init_db
from app.services.alert_service import escalate_stale_alerts

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


async def _escalation_loop() -> None:
    """Runs forever in the background: every escalation_poll_interval_seconds,
    check for ACTIVE HIGH/CRITICAL alerts nobody has acknowledged in time and
    flip them to ESCALATED. This is what stops a missed alert from silently
    sitting there — see alert_service.escalate_stale_alerts."""
    while True:
        await asyncio.sleep(settings.escalation_poll_interval_seconds)
        db = SessionLocal()
        try:
            escalated = escalate_stale_alerts(db, settings.escalation_seconds)
            if escalated:
                logger.info("Auto-escalated %d stale alert(s)", len(escalated))
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(_escalation_loop())
    logger.info("%s started (environment=%s)", settings.app_name, settings.environment)
    yield
    task.cancel()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(videos.router)
app.include_router(events.router)
app.include_router(products.router)
app.include_router(passports.router)
app.include_router(alerts.router)
app.include_router(dashboard.router)
app.include_router(assistant.router)
app.include_router(reports.router)
app.include_router(accelerometer.router)  # Workstream 5: live drop-test phone telemetry

# Serve frontend/public/ (accelerometer.html for the live drop-test demo) so
# a phone can load it same-origin as the /api/accelerometer endpoint.
_static_dir = Path(__file__).resolve().parents[2] / "frontend" / "public"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
