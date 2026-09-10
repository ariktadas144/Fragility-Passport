"""Integration tests for the aggregate-only dashboard endpoints."""
from app.models.behavior import Behavior


def _seed_behavior(db_session):
    db_session.add(Behavior(code="product_thrown", label="Throwing", category="kinetic", default_severity=5))
    db_session.commit()


def test_summary_on_empty_database(client):
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total_events"] == 0
    assert body["events_by_dock"] == {}


def test_summary_reflects_posted_events(client, db_session):
    _seed_behavior(db_session)
    client.post(
        "/events",
        json={
            "event_id": "EVT_DASH_01", "start_time": "0", "end_time": "5",
            "behavior": ["product_thrown"], "confidence": 0.9, "dock": "06",
        },
    )

    response = client.get("/dashboard/summary")
    body = response.json()
    assert body["total_events"] == 1
    assert body["events_by_dock"] == {"06": 1}
    assert body["active_alerts"] == 1  # severity-5 behavior at high confidence -> alert-worthy


def test_training_gaps_endpoint_responds(client, db_session):
    _seed_behavior(db_session)
    client.post(
        "/events",
        json={
            "event_id": "EVT_DASH_02", "start_time": "0", "end_time": "5",
            "behavior": ["product_thrown"], "confidence": 0.9, "dock": "06",
        },
    )
    response = client.get("/dashboard/training-gaps")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
