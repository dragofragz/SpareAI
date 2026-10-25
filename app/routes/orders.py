"""
Order routes — checkout, order listing, order detail, status advancement.
"""

from fastapi import APIRouter, Request, Form, Depends
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.models import SparePart, Order, OrderItem, Workshop, User
from app.templating import render
from app.utils import flash

router = APIRouter()

STATUSES = ["Placed", "Confirmed", "Shipped", "Delivered"]


@router.get("/checkout")
def checkout_page(request: Request, db: Session = Depends(get_db)):
    """Show checkout page with cart summary and workshop selection."""
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)

    cart = request.session.get("cart", [])
    cart_items = []
    total = 0.0

    for item in cart:
        part = db.query(SparePart).filter(SparePart.part_id == item["part_id"]).first()
        if part:
            subtotal = part.price * item["qty"]
            cart_items.append({"part": part, "qty": item["qty"], "subtotal": subtotal})
            total += subtotal

    if not cart_items:
        flash(request, "Your cart is empty.", "warning")
        return RedirectResponse("/cart", status_code=303)

    workshops = db.query(Workshop).all()

    return render(
        request,
        "checkout.html",
        db,
        cart_items=cart_items,
        total=total,
        workshops=workshops,
    )


@router.post("/checkout")
def checkout_submit(
    request: Request,
    workshop_id: int = Form(0),
    address: str = Form(""),
    db: Session = Depends(get_db),
):
    """Process the checkout — create order, order items, and decrement stock."""
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)

    cart = request.session.get("cart", [])
    if not cart:
        flash(request, "Your cart is empty.", "warning")
        return RedirectResponse("/cart", status_code=303)

    # Build cart items and calculate total
    calculated_total = 0.0
    valid_items = []
    for item in cart:
        part = db.query(SparePart).filter(SparePart.part_id == item["part_id"]).first()
        if part:
            calculated_total += part.price * item["qty"]
            valid_items.append({"part_id": item["part_id"], "qty": item["qty"], "price": part.price})

    if not valid_items:
        flash(request, "No valid items in your cart.", "warning")
        return RedirectResponse("/cart", status_code=303)

    order = Order(
        user_id=request.session["user_id"],
        workshop_id=workshop_id if workshop_id > 0 else None,
        status="Placed",
        total=calculated_total,
    )
    db.add(order)
    db.flush()

    for vi in valid_items:
        order_item = OrderItem(
            order_id=order.order_id,
            part_id=vi["part_id"],
            qty=vi["qty"],
            price=vi["price"],
        )
        db.add(order_item)

        # Decrement stock
        part = db.query(SparePart).filter(SparePart.part_id == vi["part_id"]).first()
        if part:
            part.stock_qty = max(0, part.stock_qty - vi["qty"])

    # Clear cart
    request.session["cart"] = []
    db.commit()

    flash(request, "Order placed successfully!", "success")
    return RedirectResponse(f"/order/{order.order_id}", status_code=303)


@router.get("/orders")
def orders_list(request: Request, db: Session = Depends(get_db)):
    """List all orders for the current user."""
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)

    orders = (
        db.query(Order)
        .filter(Order.user_id == request.session["user_id"])
        .order_by(Order.created_at.desc())
        .all()
    )
    return render(request, "orders.html", db, orders=orders)


@router.get("/order/{order_id}")
def order_detail(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Show full details for a single order."""
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)

    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        flash(request, "Order not found.", "error")
        return RedirectResponse("/orders", status_code=303)

    # Verify ownership or admin
    user = db.query(User).filter(User.user_id == request.session["user_id"]).first()
    if order.user_id != request.session["user_id"] and (not user or not user.is_admin):
        flash(request, "Access denied.", "error")
        return RedirectResponse("/orders", status_code=303)

    current_idx = STATUSES.index(order.status) if order.status in STATUSES else 0

    return render(
        request,
        "order_detail.html",
        db,
        order=order,
        statuses=STATUSES,
        current_idx=current_idx,
    )


@router.post("/order/{order_id}/advance")
def order_advance(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Advance an order to the next status in the pipeline."""
    if not request.session.get("user_id"):
        return RedirectResponse("/login", status_code=303)

    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        flash(request, "Order not found.", "error")
        return RedirectResponse("/orders", status_code=303)

    # Verify ownership or admin
    user = db.query(User).filter(User.user_id == request.session["user_id"]).first()
    if order.user_id != request.session["user_id"] and (not user or not user.is_admin):
        flash(request, "Access denied.", "error")
        return RedirectResponse("/orders", status_code=303)

    current_idx = STATUSES.index(order.status) if order.status in STATUSES else 0
    if current_idx < len(STATUSES) - 1:
        order.status = STATUSES[current_idx + 1]
        db.commit()

    flash(request, f"Order status updated to {order.status}.", "success")
    return RedirectResponse(f"/order/{order_id}", status_code=303)
