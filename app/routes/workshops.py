"""
Workshop & supplier locator routes with map data.
"""

import json

from fastapi import APIRouter, Request, Depends, Query
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.models import Workshop, Supplier
from app.templating import render
from app.utils import flash, haversine

router = APIRouter()


@router.get("/workshops")
def workshops_page(
    request: Request,
    lat: float = Query(9.684),
    lng: float = Query(76.335),
    db: Session = Depends(get_db),
):
    """Show nearby workshops and suppliers with distances on a Leaflet map."""
    # Workshops with distance
    all_workshops = db.query(Workshop).all()
    workshops_list = []
    workshops_data = []
    for w in all_workshops:
        dist = haversine(lat, lng, w.lat, w.lng)
        workshops_list.append((w, dist))
        workshops_data.append({
            "id": w.workshop_id,
            "name": w.name,
            "lat": w.lat,
            "lng": w.lng,
            "address": w.address,
            "contact": w.contact,
            "verified": w.verified,
            "rating": w.rating,
            "distance": dist,
        })
    workshops_list.sort(key=lambda x: x[1])
    workshops_data.sort(key=lambda x: x["distance"])

    # Suppliers with distance
    all_suppliers = db.query(Supplier).all()
    suppliers_list = []
    suppliers_data = []
    for s in all_suppliers:
        dist = haversine(lat, lng, s.lat, s.lng)
        suppliers_list.append((s, dist))
        suppliers_data.append({
            "id": s.supplier_id,
            "name": s.name,
            "lat": s.lat,
            "lng": s.lng,
            "address": s.address,
            "contact": s.contact,
            "distance": dist,
        })
    suppliers_list.sort(key=lambda x: x[1])
    suppliers_data.sort(key=lambda x: x["distance"])

    return render(
        request,
        "workshops.html",
        db,
        workshops=workshops_list,
        suppliers=suppliers_list,
        workshops_json=json.dumps(workshops_data),
        suppliers_json=json.dumps(suppliers_data),
        user_lat=lat,
        user_lng=lng,
    )
