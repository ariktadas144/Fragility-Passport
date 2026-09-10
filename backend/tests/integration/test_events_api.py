"""Integration tests: exercises POST/GET /events through the real HTTP
stack (FastAPI routing, Pydantic validation, response_model serialization) —
not just the service function directly."""
from app.models.behavior import Behavior


def _seed_behavior(db_session):
    db_session.add(Behavior(code="product_dragged", label="Dragging", category="kinetic", default_severity=3))
    db_session.commit()


def test_post_event_then_get_it_back(client, db_session):
    _seed_behavior(db_session)
    response = client.post(
        "/events",
        json={
            "event_id": "EVT_API_01",
            "start_time": "00:05",
            "end_time": "00:10",
            "behavior": ["product_dragged"],
            "confidence": 0.9,
            "dock": "07",
            "evidence": "Carton dragged across the floor.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["public_id"] == "EVT_API_01"
    assert body["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    fetched = client.get(f"/events/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["public_id"] == "EVT_API_01"


def test_post_event_with_unknown_behavior_code_is_rejected(client):
    response = client.post(
        "/events",
        json={
            "start_time": "00:05",
            "end_time": "00:10",
            "behavior": ["not_a_real_behavior"],
            "confidence": 0.9,
        },
    )
    assert response.status_code == 422  # Pydantic validation error, not a 500


def test_get_unknown_event_returns_404(client):
    response = client.get("/events/999999")
    assert response.status_code == 404


def test_list_events_filters_by_dock(client, db_session):
    _seed_behavior(db_session)
    client.post(
        "/events",
        json={
            "event_id": "EVT_DOCK_A", "start_time": "0", "end_time": "5",
            "behavior": ["product_dragged"], "confidence": 0.8, "dock": "06",
        },
    )
    client.post(
        "/events",
        json={
            "event_id": "EVT_DOCK_B", "start_time": "0", "end_time": "5",
            "behavior": ["product_dragged"], "confidence": 0.8, "dock": "09",
        },
    )

    response = client.get("/events", params={"dock": "06"})
    assert response.status_code == 200
    docks = {e["dock"] for e in response.json()}
    assert docks == {"06"}
