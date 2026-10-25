"""
Supplier portal routes — manage shop details and inventory.
"""

from fastapi import APIRouter, Request, Form, Depends
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.models import User, Supplier, SparePart, PartCompatibility
from app.templating import render
from app.utils import flash

router = APIRouter()


@router.get("/supplier/dashboard")
def supplier_dashboard(request: Request, db: Session = Depends(get_db)):
    """Supplier portal: view shop information and manage parts inventory."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login?role=supplier", status_code=303)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return RedirectResponse("/login", status_code=303)

    if user.role != "supplier" and not user.is_admin:
        flash(request, "Access restricted to registered spare parts suppliers.", "error")
        return RedirectResponse("/dashboard", status_code=303)

    # Check if user has an associated shop
    supplier = None
    if user.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.supplier_id == user.supplier_id).first()

    if not supplier:
        return render(
            request,
            "supplier_dashboard.html",
            db,
            has_shop=False,
            supplier=None,
            parts=[],
            stats={"total_parts": 0, "in_stock": 0, "out_of_stock": 0, "total_value": 0.0},
        )

    # Fetch parts belonging to this supplier
    parts = db.query(SparePart).filter(SparePart.supplier_id == supplier.supplier_id).all()

    in_stock = sum(1 for p in parts if p.stock_qty > 0)
    out_of_stock = sum(1 for p in parts if p.stock_qty <= 0)
    total_val = sum(p.price * p.stock_qty for p in parts)

    stats = {
        "total_parts": len(parts),
        "in_stock": in_stock,
        "out_of_stock": out_of_stock,
        "total_value": round(total_val, 2),
    }

    return render(
        request,
        "supplier_dashboard.html",
        db,
        has_shop=True,
        supplier=supplier,
        parts=parts,
        stats=stats,
    )


@router.post("/supplier/shop/setup")
def supplier_shop_setup(
    request: Request,
    name: str = Form(...),
    address: str = Form(...),
    contact: str = Form(...),
    lat: float = Form(9.6885),
    lng: float = Form(76.3320),
    db: Session = Depends(get_db),
):
    """Initial shop onboarding for a new supplier user."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return RedirectResponse("/login", status_code=303)

    # Create new supplier shop
    shop = Supplier(
        name=name.strip(),
        address=address.strip(),
        contact=contact.strip(),
        lat=lat,
        lng=lng,
    )
    db.add(shop)
    db.flush()

    user.supplier_id = shop.supplier_id
    user.role = "supplier"
    db.commit()

    flash(request, f"Shop '{shop.name}' registered successfully! You can now add parts to your inventory.", "success")
    return RedirectResponse("/supplier/dashboard", status_code=303)


@router.post("/supplier/shop/update")
def supplier_shop_update(
    request: Request,
    name: str = Form(...),
    address: str = Form(...),
    contact: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    db: Session = Depends(get_db),
):
    """Update existing shop information and coordinates."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.supplier_id:
        flash(request, "Shop not found.", "error")
        return RedirectResponse("/supplier/dashboard", status_code=303)

    supplier = db.query(Supplier).filter(Supplier.supplier_id == user.supplier_id).first()
    if not supplier:
        flash(request, "Supplier record missing.", "error")
        return RedirectResponse("/supplier/dashboard", status_code=303)

    supplier.name = name.strip()
    supplier.address = address.strip()
    supplier.contact = contact.strip()
    supplier.lat = lat
    supplier.lng = lng
    db.commit()

    flash(request, "Shop information and map coordinates updated successfully.", "success")
    return RedirectResponse("/supplier/dashboard", status_code=303)


@router.post("/supplier/part/add")
def supplier_part_add(
    request: Request,
    part_name: str = Form(...),
    oem_code: str = Form(""),
    price: float = Form(...),
    category: str = Form("Suspension"),
    stock_qty: int = Form(10),
    difficulty: str = Form("Medium"),
    tools_required: str = Form(""),
    video_id: str = Form(""),
    compatible_make: str = Form("Hyundai"),
    compatible_model: str = Form("i20"),
    year_from: int = Form(2014),
    year_to: int = Form(2025),
    db: Session = Depends(get_db),
):
    """Add a new spare part SKU to this supplier's shop."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.supplier_id:
        flash(request, "You must register a shop first before adding parts.", "error")
        return RedirectResponse("/supplier/dashboard", status_code=303)

    new_part = SparePart(
        part_name=part_name.strip(),
        oem_code=oem_code.strip(),
        price=max(1.0, price),
        category=category.strip(),
        supplier_id=user.supplier_id,
        stock_qty=max(0, stock_qty),
        difficulty=difficulty,
        tools_required=tools_required.strip(),
        video_id=video_id.strip() if video_id else None,
        image_url="https://images.unsplash.com/photo-1486006920555-c77dce18193b",
    )
    db.add(new_part)
    db.flush()

    # Add default vehicle compatibility if provided
    if compatible_make and compatible_model:
        compat = PartCompatibility(
            part_id=new_part.part_id,
            make=compatible_make.strip(),
            model=compatible_model.strip(),
            year_from=year_from,
            year_to=year_to,
        )
        db.add(compat)

    db.commit()
    flash(request, f"Spare part '{new_part.part_name}' added to your shop inventory.", "success")
    return RedirectResponse("/supplier/dashboard", status_code=303)


@router.post("/supplier/part/update")
def supplier_part_update(
    request: Request,
    part_id: int = Form(...),
    stock_qty: int = Form(...),
    price: float = Form(...),
    db: Session = Depends(get_db),
):
    """Update stock quantity and retail price of an existing part."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.supplier_id:
        return RedirectResponse("/login", status_code=303)

    part = db.query(SparePart).filter(SparePart.part_id == part_id).first()
    if not part or (part.supplier_id != user.supplier_id and not user.is_admin):
        flash(request, "You do not have permission to modify this part.", "error")
        return RedirectResponse("/supplier/dashboard", status_code=303)

    part.stock_qty = max(0, stock_qty)
    part.price = max(1.0, price)
    db.commit()

    flash(request, f"Updated '{part.part_name}': Stock = {part.stock_qty}, Price = ₹{part.price:.2f}", "success")
    return RedirectResponse("/supplier/dashboard", status_code=303)


@router.post("/supplier/part/delete")
def supplier_part_delete(
    request: Request,
    part_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """Remove a part from the supplier's inventory."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.supplier_id:
        return RedirectResponse("/login", status_code=303)

    part = db.query(SparePart).filter(SparePart.part_id == part_id).first()
    if not part or (part.supplier_id != user.supplier_id and not user.is_admin):
        flash(request, "You do not have permission to delete this part.", "error")
        return RedirectResponse("/supplier/dashboard", status_code=303)

    db.delete(part)
    db.commit()

    flash(request, "Part removed from shop inventory.", "success")
    return RedirectResponse("/supplier/dashboard", status_code=303)
