# ML → Backend Contract

This is the handoff document for the DS/ML and VLM workstreams: exactly
what JSON to `POST /events` (or hand to `scripts/process_video.py` /
`scripts/import_events.py`) so a detection becomes a risk-scored,
passport-checked, alert-worthy incident in the backend.

## Why it looks the way it does

The field names below are copied **verbatim** from `ml/vlm`'s existing
Gemini notebook's output (`event_id`, `start_time`, `end_time`, `behavior`,
`risk_level`, `risk_score`, `evidence`, `potential_consequence`,
`recommended_action`, `confidence`, `status`). That means
`warehouse_event_log.json`, as the notebook already produces it today, can
be posted to this API with **zero transformation**. Everything past that is
additive — optional fields for the kinetic/spatial detection modules
(`ml/behavior/*`) that don't exist yet, so those teams have a contract to
build against without waiting on this backend.

## Request: `POST /events`

```json
{
  "event_id": "EVT_001",
  "video_id": null,
  "source_clip_ref": "Throwing Mattresses.mp4",
  "dock": "06",

  "product_sku": "MATTRESS-001",
  "product_id": null,

  "start_time": "00:12",
  "end_time": "00:18",

  "behavior": ["product_thrown"],

  "risk_level": "HIGH",
  "risk_score": 85,
  "confidence": 0.95,

  "evidence": "A mattress is visibly thrown during unloading.",
  "potential_consequence": ["product_damage"],
  "recommended_action": "Use suitable handling equipment instead of throwing products.",
  "status": "observed_behaviour",

  "tilt_deg": null,
  "drop_height_cm": null,
  "velocity_mps": null,
  "impact_deceleration_mps2": null,
  "overlap_ratio": null,
  "overlap_duration_seconds": null,

  "evidence_frame_path": null
}
```

| field | required | notes |
|---|---|---|
| `event_id` | no | e.g. `EVT_001`. Auto-generated if omitted; if it collides with an existing one, a fresh id is generated rather than erroring. |
| `video_id` | no | if you already registered the clip via `POST /videos`. |
| `source_clip_ref` | no | the clip's filename/id — used to look up or auto-create a `Video` row if `video_id` isn't given. |
| `dock` | no | free-text dock identifier. |
| `product_sku` / `product_id` | no | either resolves the product; omit both if the product isn't identified yet. |
| `start_time` / `end_time` | **yes** | `"mm:ss"`, `"hh:mm:ss"`, or a plain number of seconds. Must satisfy `end >= start`, and must fall inside the video's `duration_seconds` if one was registered. |
| `behavior` | **yes**, min 1 | list of codes from the fixed vocabulary below. **Multi-label is supported and expected** — one timestamp can carry 2+ behaviors. |
| `risk_level` | no | `LOW`\|`MEDIUM`\|`HIGH`\|`CRITICAL`. This is treated as the *upstream model's opinion*, not the final answer — the backend recalibrates it against the product's Fragility Passport. |
| `risk_score` | no | 0–100. If omitted, the backend derives a fallback from the worst behavior's default severity. |
| `confidence` | **yes** | 0–1. |
| `evidence` | no | plain-language description — shown on the dashboard and in the PDF report. |
| `potential_consequence` | no | free-text list. |
| `recommended_action` | no | free-text. |
| `status` | no, default `observed_behaviour` | `observed_behaviour` \| `potential_risk` \| `confirmed_damage`. |
| `tilt_deg`, `drop_height_cm`, `velocity_mps`, `impact_deceleration_mps2` | no | kinetic module fields (`ml/behavior/kinetic.py`, not yet built). Compared directly against the product's passport limits when present. |
| `overlap_ratio`, `overlap_duration_seconds` | no | static/configuration module fields (`ml/behavior/stacking.py`, `spatial.py`, not yet built). |
| `evidence_frame_path` | no | absolute path to a saved frame/clip already on disk; gets copied into the managed evidence directory and linked to the event. |

## Behavior vocabulary

All values in `app/core/constants.py::BEHAVIOR_VOCABULARY`, seeded into the
`behaviors` table:

`product_dropped`, `product_dragged`, `product_thrown`, `product_rolling`,
`rough_handling`, `improper_stacking`, `unstable_stacking`,
`product_outside_designated_area`, `improper_equipment_usage`,
`unsafe_loading_sequence` (the VLM notebook's original 10), plus
`wrong_orientation`, `stepping_on_product`, `dock_vehicle_gap`,
`uneven_dock_level` (added to cover the master plan's full ground-truth
taxonomy). Sending any other string is a `422` validation error — this is a
closed vocabulary by design, matching the VLM notebook's own philosophy of
never letting the model invent categories.

## What happens after ingestion

1. Timestamps are parsed and validated.
2. The product (if given) and its Fragility Passport are looked up.
3. The risk engine recalculates `risk_score`/`risk_level` — see
   [risk-engine.md](risk-engine.md) — and checks the passport contract
   (e.g. was throwing detected on a product whose passport prohibits it).
4. The Event, its behavior links, and any evidence file are persisted.
5. If the final risk is MEDIUM or above, an Alert is created automatically.

## Batch / offline paths

- `scripts/import_events.py path/to/warehouse_event_log.json` — imports a
  VLM notebook output file (or any file matching `{"events": [...]}` or a
  bare list) as-is.
- `scripts/process_video.py video.mp4 pipeline_output.json` — the same
  idea, framed as the DS/ML pipeline's hand-off point. Registers the video
  first, then imports each detection against it.

Both call the exact same `event_service.ingest_detection()` function
`POST /events` uses, so behavior is identical regardless of path.
