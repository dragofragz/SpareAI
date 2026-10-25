"""
Admin routes — executive operations portal, system diagnostics, and master controls.
"""

from fastapi import APIRouter, Request, Form, Depends
from sqlalchemy.orm import Session, joinedload
from starlette.responses import RedirectResponse
from werkzeug.security import check_password_hash

from app.database import get_db
from app.models import User, Order, SparePart, Supplier, Workshop, RepairCase
from app.templating import render
from app.utils import flash

router = APIRouter()


@router.get("/admin/login")
def admin_login_page(request: Request, db: Session = Depends(get_db)):
    """Executive high-security admin login portal."""
    user_id = request.session.get("user_id")
    if user_id:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user and user.is_admin:
            return RedirectResponse("/admin", status_code=303)
    return render(request, "admin_login.html", db)


@router.post("/admin/login")
def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Authenticate administrator credentials with role verification."""
    user = db.query(User).filter(User.email == email.strip()).first()
    if not user or not check_password_hash(user.password_hash, password):
        return render(request, "admin_login.html", db, error="Invalid administrator credentials.")

    if not user.is_admin and user.role != "admin":
        return render(request, "admin_login.html", db, error="Access Denied: Account lacks administrative privileges.")

    request.session["user_id"] = user.user_id
    flash(request, f"Welcome to SpareAI Enterprise Core, {user.name}.", "success")
    return RedirectResponse("/admin", status_code=303)


@router.get("/admin")
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Executive admin dashboard with system KPIs, order flow, supplier network, and inventory."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/admin/login", status_code=303)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.is_admin:
        flash(request, "Administrative privileges required.", "error")
        return RedirectResponse("/admin/login", status_code=303)

    orders = (
        db.query(Order)
        .options(joinedload(Order.user), joinedload(Order.items), joinedload(Order.workshop))
        .order_by(Order.created_at.desc())
        .all()
    )

    parts = db.query(SparePart).options(joinedload(SparePart.supplier)).all()
    suppliers = db.query(Supplier).all()
    workshops = db.query(Workshop).all()
    users = db.query(User).all()
    cases_count = db.query(RepairCase).count()

    total_revenue = sum(o.total for o in orders)
    in_stock_parts = sum(1 for p in parts if p.stock_qty > 0)
    out_of_stock_parts = sum(1 for p in parts if p.stock_qty <= 0)

    stats = {
        "total_orders": len(orders),
        "total_revenue": round(total_revenue, 2),
        "total_users": len(users),
        "total_parts": len(parts),
        "in_stock_parts": in_stock_parts,
        "out_of_stock_parts": out_of_stock_parts,
        "total_suppliers": len(suppliers),
        "total_workshops": len(workshops),
        "cbr_cases": cases_count,
    }

    return render(
        request,
        "admin_dashboard.html",
        db,
        orders=orders,
        parts=parts,
        suppliers=suppliers,
        workshops=workshops,
        users=users,
        stats=stats,
    )


@router.post("/admin/stock/update")
def update_stock(
    request: Request,
    part_id: int = Form(...),
    stock_qty: int = Form(...),
    price: float = Form(None),
    db: Session = Depends(get_db),
):
    """Update stock quantity and optional price from master inventory."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/admin/login", status_code=303)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.is_admin:
        flash(request, "Admin access required.", "error")
        return RedirectResponse("/admin/login", status_code=303)

    part = db.query(SparePart).filter(SparePart.part_id == part_id).first()
    if not part:
        flash(request, "Part not found.", "error")
        return RedirectResponse("/admin", status_code=303)

    part.stock_qty = max(0, stock_qty)
    if price is not None and price > 0:
        part.price = price
    db.commit()

    flash(request, f"Updated '{part.part_name}': Stock = {part.stock_qty}, Price = ₹{part.price:.2f}", "success")
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/order/{order_id}/status")
def admin_order_status(
    order_id: int,
    request: Request,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    """Directly override and change order status from the admin console."""
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/admin/login", status_code=303)

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.is_admin:
        flash(request, "Admin access required.", "error")
        return RedirectResponse("/admin/login", status_code=303)

    order = db.query(Order).filter(Order.order_id == order_id).first()
    if order and status in ["Placed", "Confirmed", "Shipped", "Delivered"]:
        order.status = status
        db.commit()
        flash(request, f"Order #{order_id} status updated to '{status}'.", "success")

    return RedirectResponse("/admin", status_code=303)
