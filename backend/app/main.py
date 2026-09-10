"""
Fragility Passport -- FastAPI app entrypoint.

Wires together: video upload -> detection/tracking pipeline (ml/) ->
risk classification (ml/vlm/) -> event storage -> API routes consumed
by the frontend dashboard.

Run locally:
    cd backend
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000

Then open http://localhost:8000/docs for interactive API testing.
"""

import sys
from pathlib import Path

# Allow imports of the top-level ml/ package from within backend/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import health, videos, events, passports, assistant, accelerometer

BASE_DIR = Path(__file__).parent.parent.parent

app = FastAPI(title="Fragility Passport API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for hackathon demo; tighten before anything real
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = BASE_DIR / "frontend" / "public"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(health.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(passports.router, prefix="/api")
app.include_router(assistant.router, prefix="/api")
app.include_router(accelerometer.router, prefix="/api")
