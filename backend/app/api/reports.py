"""GET /reports/{event_id} returns the auto-generated claim packet — a PDF
by default, or the same content as HTML with ?format=html for a quick
browser preview."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.core.exceptions import DomainError
from app.database.database import get_db
from app.services import event_service, report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{event_id}")
def get_report(
    event_id: int,
    output_format: str = Query(default="pdf", alias="format", pattern="^(pdf|html)$"),
    db: Session = Depends(get_db),
):
    try:
        event = event_service.get_event(db, event_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    if output_format == "html":
        return HTMLResponse(content=report_service.render_html(event))

    pdf_bytes = report_service.render_pdf(event)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{event.public_id}_report.pdf"'},
    )
