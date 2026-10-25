"""
Tutorial route — installation / repair guides for parts.
"""

from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.models import SparePart
from app.ai_engine import get_service_guidance
from app.templating import render
from app.utils import flash

router = APIRouter()


@router.get("/tutorial/{part_id}")
def tutorial(part_id: int, request: Request, db: Session = Depends(get_db)):
    """Show the installation tutorial for a spare part."""
    part = db.query(SparePart).filter(SparePart.part_id == part_id).first()
    if not part:
        flash(request, "Part not found.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    return render(
        request,
        "tutorial.html",
        db,
        part=part,
        service_guidance=get_service_guidance(part),
    )
