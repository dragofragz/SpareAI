"""
Shopping-cart routes — add, view, update, remove items (session-based).
"""

from fastapi import APIRouter, Request, Form, Depends
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.models import SparePart
from app.templating import render
from app.utils import flash

router = APIRouter()


@router.post("/cart/add")
def cart_add(
    request: Request,
    part_id: int = Form(...),
    qty: int = Form(1),
    db: Session = Depends(get_db),
):
    """Add a part to the session cart (or increment quantity if already present)."""
    cart = request.session.get("cart", [])

    found = False
    for item in cart:
        if item["part_id"] == part_id:
            item["qty"] += qty
            found = True
            break
    if not found:
        cart.append({"part_id": part_id, "qty": qty})

    # Reassign to trigger session save
    request.session["cart"] = cart
    flash(request, "Added to cart.", "success")
    referer = request.headers.get("referer", "/dashboard")
    return RedirectResponse(referer, status_code=303)


@router.get("/cart")
def view_cart(request: Request, db: Session = Depends(get_db)):
    """Display the current shopping cart."""
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

    return render(request, "cart.html", db, cart_items=cart_items, total=total)


@router.post("/cart/update")
def cart_update(
    request: Request,
    part_id: int = Form(...),
    qty: int = Form(...),
):
    """Update the quantity of a cart item, or remove it if qty <= 0."""
    cart = request.session.get("cart", [])

    if qty <= 0:
        cart = [item for item in cart if item["part_id"] != part_id]
    else:
        for item in cart:
            if item["part_id"] == part_id:
                item["qty"] = qty
                break

    request.session["cart"] = cart
    flash(request, "Cart updated.", "success")
    return RedirectResponse("/cart", status_code=303)


@router.post("/cart/remove")
def cart_remove(
    request: Request,
    part_id: int = Form(...),
):
    """Remove an item from the cart entirely."""
    cart = request.session.get("cart", [])
    cart = [item for item in cart if item["part_id"] != part_id]
    request.session["cart"] = cart
    flash(request, "Removed from cart.", "success")
    return RedirectResponse("/cart", status_code=303)
