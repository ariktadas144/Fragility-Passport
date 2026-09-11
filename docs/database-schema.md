# Database Schema

The backend uses SQLAlchemy models (`backend/app/models/`) against SQLite by
default (`DATABASE_URL` swaps it for Postgres/Supabase with no code changes
— see [deployment.md](deployment.md)).

## Tables and relationships

```
Video (1) ──< (many) Event >── (many) Product (1)
                  │                        │
                  │                        └── (1) FragilityPassport
                  │
                  ├──< EventBehavior >── Behavior
                  ├──< Evidence
                  └──< Alert
```

### `products`
| column | type | notes |
|---|---|---|
| id | int, PK | |
| sku | string, unique | e.g. `ABC-123` |
| name | string | |
| category | string | e.g. `kd-panel-furniture` |
| declared_value_inr | float | used only for the ₹ exposure estimate — see [risk-engine.md](risk-engine.md) |

### `fragility_passports`
One row per product (1:1), the "handling contract" the risk engine checks a
detection against.

| column | type | notes |
|---|---|---|
| id | int, PK | |
| product_id | int, FK → products.id, unique | |
| max_tilt_deg | float | |
| max_drop_height_cm | float | |
| required_orientation | string | `UPRIGHT` \| `FLAT` \| `ANY` |
| max_stack_weight_kg | float | |
| drag_allowed | bool | |
| throw_allowed | bool | |
| notes | text, nullable | |

### `behaviors`
The fixed vocabulary of detectable behaviors (seeded once from
`data/seed/behaviors.json`, mirrors `app/core/constants.py`).

| column | type | notes |
|---|---|---|
| id | int, PK | |
| code | string, unique | e.g. `product_dragged` — what the ML/VLM layer sends |
| label | string | human-readable |
| category | string | `kinetic` \| `static` |
| default_severity | int (1–5) | used as a risk-score fallback when no ML score is given |

### `videos`
| column | type | notes |
|---|---|---|
| id | int, PK | |
| filename | string | |
| dock | string, nullable | |
| source_clip_ref | string, nullable | join key used by `event_service._get_or_create_video` |
| duration_seconds | float, nullable | used to sanity-check event timestamps |
| fps | float, nullable | |
| status | string | `uploaded` \| `processed` |
| uploaded_at | datetime | |

### `events`
The central table — one row per risk incident.

| column | type | notes |
|---|---|---|
| id | int, PK | |
| public_id | string, unique | e.g. `EVT_001`; upstream-provided or auto-generated |
| video_id | int, FK → videos.id, nullable | |
| product_id | int, FK → products.id, nullable | |
| dock | string, nullable | |
| start_time_seconds / end_time_seconds | float | |
| risk_level | string | `LOW` \| `MEDIUM` \| `HIGH` \| `CRITICAL` — calibrated by the risk engine, not just copied from the ML/VLM input |
| risk_score | float (0–100) | |
| confidence | float (0–1) | |
| status | string | `observed_behaviour` \| `potential_risk` \| `confirmed_damage` |
| evidence_description | text, nullable | |
| potential_consequence | text, nullable | JSON-encoded list |
| recommended_action | text, nullable | |
| contract_clause_violated | text, nullable | plain-language explanation if a Fragility Passport rule was broken |
| estimated_exposure_inr | float, nullable | industry-indicative only, see risk-engine.md |
| created_at | datetime | |

### `event_behaviors`
A dedicated join table (not a bare many-to-many) between `events` and
`behaviors`, because one incident can carry 2+ simultaneous behaviors (e.g.
"throwing" + "strap misuse" on the same timestamp — a real finding from the
pilot footage).

### `evidence`
| column | type | notes |
|---|---|---|
| id | int, PK | |
| event_id | int, FK → events.id | |
| file_path | string | |
| kind | string | `frame` \| `clip` |
| captured_at | datetime | |

### `alerts`
| column | type | notes |
|---|---|---|
| id | int, PK | |
| event_id | int, FK → events.id | |
| status | string | `ACTIVE` \| `ACKNOWLEDGED` \| `ESCALATED` |
| created_at | datetime | |
| acknowledged_at / acknowledged_by | datetime / string, nullable | |
| escalated_at | datetime, nullable | set automatically if unacknowledged past `ESCALATION_SECONDS` — see `alert_service.escalate_stale_alerts` |

## Notes

- Every timestamp column uses a shared naive-UTC `utcnow()` helper
  (`app/utils/timestamps.py`) rather than timezone-aware datetimes, so
  SQLite's plain-text storage stays consistently comparable (this was a real
  bug caught and fixed during development — see git history).
- All tables are created via `Base.metadata.create_all()`
  (`app/database/database.py:init_db`) — there is no separate migration
  tool in this hackathon-scope build; schema changes require a fresh
  database (`scripts/seed_database.py` rebuilds from scratch).
