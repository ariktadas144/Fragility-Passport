# Risk Engine

Implemented in `backend/app/services/risk_service.py`. This is what turns a
generic "risky!" into "SKU-class ABC-123 violated clause X" — the core
differentiator described in the master plan.

## Why the backend recalculates risk instead of trusting the ML/VLM layer

The ML/VLM layer's `risk_score`/`risk_level` reflects what it can see in
one clip. It has no idea what the *specific product's* handling contract
actually says. The backend is the only layer that has both pieces of
information at once (the detection AND the Fragility Passport), so it's the
only layer that can produce the final, contract-aware number.

## The formula

For a detection with behaviors `B` and (optionally) a resolved product `P`
and its passport:

1. **`ml_score`** — `detection.risk_score` if the upstream layer sent one;
   otherwise falls back to `max(default_severity for b in B) × 20` (a
   severity of 1–5 maps to 20–100).
2. **`severity_score`** — `max(default_severity for b in B) × 20`, always
   computed regardless of whether an ML score was given.
3. **`confidence_score`** — `detection.confidence × 100`.
4. **Blend:**
   ```
   combined = 0.5 × ml_score + 0.3 × severity_score + 0.2 × confidence_score
   ```
   Weighted this way so the upstream model's own read carries the most
   weight, but a HIGH claim made at low confidence doesn't score identically
   to one made at high confidence, and a behavior's known severity always
   has some influence even if the model didn't report a score at all.
5. **Contract check** (`check_contract_violations`) — compares the
   detection against the product's Fragility Passport:
   - `tilt_deg` > `max_tilt_deg` → violation
   - `drop_height_cm` > `max_drop_height_cm` → violation
   - `product_dragged` present and `drag_allowed` is false → violation
   - `product_thrown` present and `throw_allowed` is false → violation
   - `wrong_orientation` present and `required_orientation != ANY` → violation

   Each violation produces a plain-language string, e.g.:
   > "SKU-class ABC-123: tilt exceeded 40°. Contract requires upright transport only."

   (This is the README's own worked example, reproducible for real via
   `data/seed/pilot_events.json` + `data/seed/fragility_passports.json`.)

6. **If any violation fired:** `combined = min(100, combined + 20)` — a
   confirmed contract breach isn't "maybe risky," it's a full tier worse.
7. **Risk level** — the highest threshold the final score clears:

   | level | minimum score |
   |---|---|
   | LOW | 0 |
   | MEDIUM | 40 |
   | HIGH | 65 |
   | CRITICAL | 85 |

## ₹ exposure estimate

```
estimated_exposure_inr = product.declared_value_inr × multiplier[risk_level]
```
| risk level | multiplier |
|---|---|
| LOW | 0.05 |
| MEDIUM | 0.15 |
| HIGH | 0.35 |
| CRITICAL | 0.65 |

**This is explicitly an industry-indicative estimate, not an audited
valuation** — it exists to show the scale of the problem in ₹ terms (the
master plan's "Damage Prevention & Business Impact" is 20% of the judging
weight), not as a Godrej-specific guarantee. Every place this number
surfaces (API response, PDF report, dashboard) should be presented with
that caveat, per the master plan's own honesty checklist.

## Alert threshold

An `Alert` is created automatically for any event scoring `MEDIUM` or
above (`alert_service.ALERT_WORTHY_LEVELS`). `HIGH`/`CRITICAL` alerts that
go unacknowledged for `ESCALATION_SECONDS` (default 15s) auto-escalate via
a background timer in `main.py` — this is the direct fix for the master
plan's clip where a supervisor was present and still missed the event: the
system no longer depends on a human noticing in time.
