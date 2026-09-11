# Frontend

Next.js (App Router) dashboard for Fragility Passport. Pages read live data
from the FastAPI backend — see [`../backend/README.md`](../backend/README.md).

## Run it

```bash
cp .env.example .env.local          # set NEXT_PUBLIC_API_BASE_URL if the backend isn't on :8000
npm install
npm run dev                          # http://localhost:3000
```

The backend must be running (`cd ../backend && uvicorn app.main:app`) and
seeded (`python ../scripts/seed_database.py`) or pages render with an
"could not reach the backend" notice.

## What's wired to the backend

| Page | Endpoint(s) | Notes |
|---|---|---|
| `/` (Dashboard) | `GET /dashboard/summary`, `GET /events` | risk counts, ₹ exposure, alert counts, recent HIGH/CRITICAL incidents |
| `/incidents` | `GET /events` → `GET /events/{id}` | full rows incl. `contract_clause_violated`, `estimated_exposure_inr`, product |
| `/monitor` | `GET /events` | per-dock incident counts + highest-risk event; no video streaming in this build |
| `/passports` | `GET /products` → `GET /passports/{id}` | handling contracts; client-side SKU/name search |
| `/analytics` | `GET /dashboard/summary` | bar = incidents per dock, donut = incidents per risk level; both reshaped client-side from the one summary payload |
| ChatWidget | `POST /assistant/query` | grounded Q&A; renders the answer + its `source` (`local` / `llm` / `unavailable`) |

All API access goes through [`src/lib/api.ts`](src/lib/api.ts).
`NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`) is the only config.
