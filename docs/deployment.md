# Deployment

## Local development

```bash
cd backend
python3.12 -m venv venv          # use 3.12+, not the system python3 — see note below
source venv/bin/activate
pip install -r requirements.txt
python ../scripts/seed_database.py   # optional: populate with real pilot data
uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`; interactive docs at
`http://localhost:8000/docs`.

**Python version note:** this codebase uses modern type-hint syntax
(`str | None`), which requires **Python 3.10+**. On macOS, the default
`python3` is often an old system install (3.9) — check with `python3
--version` first. If you're on 3.9, install a newer version via Homebrew
(`brew install python@3.12`) and create the venv with that binary instead.

## Environment variables

Copy `.env.example` to `.env` in `backend/` and adjust as needed. See that
file for the full list — nothing is required for local/demo use; every
setting has a sane default (SQLite file, no API key, permissive CORS).

## Docker Compose

```bash
docker-compose up -d
```

Builds and runs the backend from `backend/Dockerfile`, on port 8000, with
its SQLite database and evidence files persisted in named Docker volumes
(`backend_db`, `backend_evidence`) so they survive container restarts.

To seed the containerized database:
```bash
docker-compose exec backend python ../scripts/seed_database.py
```

An optional Postgres service is included commented-out in
`docker-compose.yml`, for anyone who wants to run against Postgres/Supabase
instead of SQLite — uncomment it, point `DATABASE_URL` at it, and add a
Postgres driver (`pip install "psycopg[binary]"`) to `backend/requirements.txt`.

A placeholder for Workstream 3's frontend service is also left
commented-out in the same file.

## Deploying the backend (Render / Railway free tier)

Both platforms follow the same shape, per the master plan's "free tools"
guidance:

1. Connect the GitHub repo, point the service at the `backend/` directory.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set environment variables from `.env.example` as needed (at minimum,
   nothing — defaults work for a demo).
5. **Important:** both platforms' free tiers use an *ephemeral* filesystem —
   anything written to disk (the SQLite file, evidence frames) is lost on
   redeploy/restart. For a throwaway hackathon demo this is usually fine
   (reseed on boot), but for anything meant to persist, switch
   `DATABASE_URL` to a managed Postgres instance (Render/Railway both offer
   a free Postgres add-on) rather than relying on the local SQLite file.

## Running the test suite

```bash
cd backend
pytest
```

Tests run against a dedicated throwaway SQLite file
(`backend/test_fragility_passport.db`, gitignored), never the real
development database — see `backend/tests/conftest.py`.
