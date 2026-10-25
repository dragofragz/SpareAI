"""
Dashboard routes — overview, vehicle add / delete.
"""

from fastapi import APIRouter, Request, Form, Depends
from sqlalchemy.orm import Session, joinedload
from starlette.responses import RedirectResponse

from app.database import get_db
from app.models import User, Vehicle, Fault, Order
from app.templating import render
from app.utils import flash

router = APIRouter()


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    """Main dashboard showing vehicles, recent faults, and recent orders."""
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)

    user_id = request.session["user_id"]
    user = db.query(User).filter(User.user_id == user_id).first()
    if user and user.role == "supplier":
        return RedirectResponse("/supplier/dashboard", status_code=303)
    if user and user.role == "admin" and not user.vehicles:
        return RedirectResponse("/admin", status_code=303)

    vehicles = (
        db.query(Vehicle)
        .options(joinedload(Vehicle.faults))
        .filter(Vehicle.user_id == user_id)
        .all()
    )

    recent_faults = (
        db.query(Fault)
        .join(Vehicle)
        .filter(Vehicle.user_id == user_id)
        .order_by(Fault.created_at.desc())
        .limit(5)
        .all()
    )

    recent_orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )

    return render(
        request,
        "dashboard.html",
        db,
        vehicles=vehicles,
        recent_faults=recent_faults,
        recent_orders=recent_orders,
    )


@router.post("/vehicle/add")
def add_vehicle(
    request: Request,
    vehicle_type: str = Form(...),
    make: str = Form(...),
    model: str = Form(...),
    year: int = Form(...),
    vin: str = Form(""),
    db: Session = Depends(get_db),
):
    """Add a new vehicle for the current user."""
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)

    vehicle = Vehicle(
        user_id=request.session["user_id"],
        type=vehicle_type,
        make=make,
        model=model,
        year=year,
        vin=vin,
    )
    db.add(vehicle)
    db.commit()
    flash(request, "Vehicle added successfully.", "success")
    return RedirectResponse("/dashboard", status_code=303)


@router.get("/vehicle/{vehicle_id}/delete")
def delete_vehicle(
    vehicle_id: int, request: Request, db: Session = Depends(get_db)
):
    """Delete a vehicle belonging to the current user."""
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)

    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle or vehicle.user_id != request.session["user_id"]:
        flash(request, "Vehicle not found.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    db.delete(vehicle)
    db.commit()
    flash(request, "Vehicle deleted.", "success")
    return RedirectResponse("/dashboard", status_code=303)
