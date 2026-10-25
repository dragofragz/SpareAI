"""
Part detail route — view a spare part with stock and compatibility info.
"""

from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.models import SparePart, Supplier, PartCompatibility, Vehicle
from app.ai_engine import get_service_guidance
from app.templating import render
from app.utils import flash

router = APIRouter()


@router.get("/part/{part_id}")
def part_detail(
    part_id: int,
    request: Request,
    vehicle_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """Show detailed information for a spare part, including stock across suppliers."""
    part = db.query(SparePart).filter(SparePart.part_id == part_id).first()
    if not part:
        flash(request, "Part not found.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    # Stock info: find all SpareParts with the same part_name across suppliers
    same_name_parts = (
        db.query(SparePart)
        .filter(SparePart.part_name == part.part_name)
        .all()
    )
    stock_info = []
    seen_suppliers = set()
    for p in same_name_parts:
        if p.supplier_id and p.supplier_id not in seen_suppliers:
            sup = db.query(Supplier).filter(Supplier.supplier_id == p.supplier_id).first()
            if sup:
                stock_info.append({
                    "supplier_name": sup.name,
                    "supplier_id": sup.supplier_id,
                    "qty": p.stock_qty,
                    "lat": sup.lat,
                    "lng": sup.lng,
                    "contact": sup.contact,
                    "address": sup.address,
                })
                seen_suppliers.add(p.supplier_id)

    # Optional vehicle compatibility check
    vehicle_obj = None
    compatible = None
    if vehicle_id is not None:
        vehicle_obj = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
        if vehicle_obj:
            compat = (
                db.query(PartCompatibility)
                .filter(
                    PartCompatibility.part_id == part_id,
                    PartCompatibility.make.ilike(vehicle_obj.make),
                    PartCompatibility.model.ilike(vehicle_obj.model),
                    PartCompatibility.year_from <= vehicle_obj.year,
                    PartCompatibility.year_to >= vehicle_obj.year,
                )
                .first()
            )
            compatible = compat is not None

    return render(
        request,
        "part_detail.html",
        db,
        part=part,
        stock_info=stock_info,
        vehicle=vehicle_obj,
        compatible=compatible,
        service_guidance=get_service_guidance(part),
    )
