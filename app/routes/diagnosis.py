"""
Diagnosis routes — fault input and AI-powered results.
"""

from fastapi import APIRouter, Request, Form, Depends
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.models import Vehicle, Fault
from app.ai_engine import recommend_parts
from app.templating import render
from app.utils import flash

router = APIRouter()


@router.get("/diagnose/{vehicle_id}")
def diagnose_form(vehicle_id: int, request: Request, db: Session = Depends(get_db)):
    """Show the fault description input form for a vehicle."""
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)

    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle or vehicle.user_id != request.session["user_id"]:
        flash(request, "Vehicle not found.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    return render(request, "fault_input.html", db, vehicle=vehicle)


@router.post("/diagnose/{vehicle_id}")
def diagnose_submit(
    vehicle_id: int,
    request: Request,
    description: str = Form(...),
    db: Session = Depends(get_db),
):
    """Record a new fault and redirect to results."""
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)

    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle or vehicle.user_id != request.session["user_id"]:
        flash(request, "Vehicle not found.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    fault = Fault(vehicle_id=vehicle_id, description=description)
    db.add(fault)
    db.commit()
    db.refresh(fault)
    return RedirectResponse(f"/results/{fault.fault_id}", status_code=303)


@router.get("/results/{fault_id}")
def results(fault_id: int, request: Request, db: Session = Depends(get_db)):
    """Display AI-recommended parts for a diagnosed fault."""
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)

    fault = db.query(Fault).filter(Fault.fault_id == fault_id).first()
    if not fault:
        flash(request, "Fault not found.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    vehicle = fault.vehicle

    results = recommend_parts(
        db,
        fault.description,
        vehicle.type,
        vehicle.make,
        vehicle.model,
        vehicle.year,
    )

    return render(
        request,
        "diagnosis_results.html",
        db,
        fault=fault,
        vehicle=vehicle,
        results=results,
    )
