"""Integration tests for the auto-generated claim-packet report endpoint."""
from app.models.behavior import Behavior


def _seed_and_post_event(client, db_session) -> int:
    db_session.add(Behavior(code="product_dragged", label="Dragging", category="kinetic", default_severity=3))
    db_session.commit()

    response = client.post(
        "/events",
        json={
            "event_id": "EVT_REPORT_01", "start_time": "00:05", "end_time": "00:10",
            "behavior": ["product_dragged"], "confidence": 0.9, "dock": "07",
            "evidence": "Carton dragged across the floor.",
        },
    )
    return response.json()["id"]


def test_get_report_returns_pdf_by_default(client, db_session):
    event_id = _seed_and_post_event(client, db_session)
    response = client.get(f"/reports/{event_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_get_report_html_preview(client, db_session):
    event_id = _seed_and_post_event(client, db_session)
    response = client.get(f"/reports/{event_id}", params={"format": "html"})
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "EVT_REPORT_01" in response.text


def test_get_report_for_unknown_event_returns_404(client):
    response = client.get("/reports/999999")
    assert response.status_code == 404
