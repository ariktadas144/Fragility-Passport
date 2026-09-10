# Backend

FastAPI backend for Fragility Passport (Workstream 4), with the ML/detection
pipeline (Workstream 5) wired into it.

## Architecture

```text
                          ml/pipeline/orchestrator.py
  clip.mp4  ──►  YOLO + ByteTrack          (ml/pipeline/video_pipeline.py)
                 ├─ per-track kinematics    (ml/behavior/kinetic.py)
                 │    └─ risk classify      (ml/vlm/classifier.py)
                 ├─ Gemini whole-video      (ml/vlm/gemini_analysis.py)
                 └─ cross-validation fusion (ml/behavior/fusion.py)
                          │
                          ▼  fused events
                 ml/pipeline/backend_client.py
                          │  POST /events   (one call per fused event)
                          ▼
   ┌──────────────────────────────────────────────────────────────┐
   │  this backend  (backend/app)                                  │
   │   /events  ─►  risk engine recalibrates vs. Fragility Passport │
   │            ─►  contract-violation check, ₹ exposure estimate   │
   │            ─►  Event + behaviors persisted (SQLite)            │
   │            ─►  Alert auto-created if final risk ≥ MEDIUM       │
   │  /alerts /dashboard /passports /reports /assistant /products   │
   │  /api/accelerometer  ◄── phone drop-test telemetry (WS5)       │
   └──────────────────────────────────────────────────────────────┘
```

### Why one backend

Workstream 5 originally shipped its own thin storage/API layer
(`data/processed/<job>/summary.json` + a parallel set of `/api/*` routes).
Workstream 4's backend is the production one — real SQLAlchemy models, a
risk engine that recalibrates against each product's Fragility Passport,
auto-escalating alerts, PDF/HTML reports, a grounded assistant, and a test
suite. Its `POST /events` is explicitly designed as the ML pipeline's front
door (`docs/ml-backend-contract.md`).

So the pipeline no longer stores or serves anything itself. It runs
detection + fusion and POSTs each fused event to `/events`; the backend is
the single system of record. The only Workstream-5 route that survived is
`/api/accelerometer/{job_id}` (phone sensor logging for the live drop-test
demo — nothing on the backend side covers it). It keeps the `/api` prefix
to match the frozen `frontend/public/accelerometer.html`.

## Run it

```bash
cd backend
pip install -r requirements.txt          # includes the ml/ pipeline deps
python ../scripts/seed_database.py        # products, passports, behaviors, pilot events
uvicorn app.main:app --reload             # http://localhost:8000/docs
```

## Feed a video through the pipeline

With the backend running:

```bash
# from the repo root
python -m ml.pipeline.orchestrator path/to/clip.mp4 --dock 06 --product-sku ABC-123
```

- `--product-sku` is what unlocks the Fragility Passport contract check and
  the ₹ exposure estimate — without it the event is still scored, just not
  passport-checked.
- `--no-submit` runs detection + fusion only and writes
  `data/processed/<clip>/fusion_debug.json` without touching the backend.
- Gemini is best-effort: if `GEMINI_API_KEY` is unset or Gemini's video API
  fails, the run completes on kinematics alone (`gemini_error` is recorded).

### Config (env / `backend/.env`)

| var | default | purpose |
|---|---|---|
| `GEMINI_API_KEY` | — | Gemini whole-video analysis. Read from `backend/.env` automatically. |
| `BACKEND_URL` | `http://localhost:8000` | where `backend_client` POSTs events |
| `BACKEND_API_KEY` | — | sent as `X-API-Key`; only needed if the backend sets `API_KEY` |
| `GEMINI_VIDEO_PROCESSING_TIMEOUT` | `180` | seconds to wait for Gemini's Files API before falling back |

## Known rough edges

- **SQLite dev DB** (`backend/fragility_passport.db`). Fine for the demo;
  point `DATABASE_URL` at Postgres for anything real.
- **CORS** is limited to localhost dev origins in `app/config.py` — add the
  deployed frontend origin before deploying.
- **Gemini's video path is flaky right now** — the same clip intermittently
  comes back `FAILED` / `503` / a Files-API `500` while plain text calls on
  the same key succeed. `gemini_analysis.py` retries transient errors and
  re-uploads once on `FAILED`; past that, the pipeline falls back to
  kinematics-only rather than failing the job.
- **`reports/` HTML preview** has one failing test on Python 3.14
  (`test_get_report_html_preview`) — a Jinja/template rendering issue in
  Workstream 4's report layer, unrelated to event ingestion. Passes on the
  CI-pinned Python 3.12.
- The kinematics classifier (`ml/vlm/classifier.py`) is still a velocity/drop
  heuristic on stock-YOLO (COCO) tracks, not the fine-tuned warehouse model.
  It emits real behavior codes and real events, but "dragging" currently
  means "something moved fast horizontally", not "a carton was dragged".
