"""
About page route.
"""

from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.templating import render

router = APIRouter()


@router.get("/about")
def about(request: Request, db: Session = Depends(get_db)):
    """Render the about / information page."""
    return render(request, "about.html", db)
