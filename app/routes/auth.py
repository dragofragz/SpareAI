"""
Authentication routes — login, register, logout with role-based routing.
"""

from fastapi import APIRouter, Request, Form, Depends, Query
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from werkzeug.security import generate_password_hash, check_password_hash

from app.database import get_db
from app.models import User
from app.templating import render
from app.utils import flash

router = APIRouter()


@router.get("/login")
def login_page(
    request: Request,
    role: str = Query("customer"),
    db: Session = Depends(get_db),
):
    """Show the login form. If already logged in, redirect to appropriate role portal."""
    user_id = request.session.get("user_id")
    if user_id:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            if user.is_admin or user.role == "admin":
                return RedirectResponse("/admin", status_code=303)
            elif user.role == "supplier":
                return RedirectResponse("/supplier/dashboard", status_code=303)
            return RedirectResponse("/dashboard", status_code=303)

    return render(request, "login.html", db, selected_role=role)


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Authenticate user credentials and route to role-specific dashboard."""
    user = db.query(User).filter(User.email == email.strip()).first()
    if user and check_password_hash(user.password_hash, password):
        request.session["user_id"] = user.user_id

        # Role-based intelligent redirection
        if user.is_admin or user.role == "admin":
            flash(request, f"Authenticated as Administrator: {user.name}", "success")
            return RedirectResponse("/admin", status_code=303)
        elif user.role == "supplier":
            flash(request, f"Welcome to Supplier Hub, {user.name}", "success")
            return RedirectResponse("/supplier/dashboard", status_code=303)
        else:
            flash(request, f"Welcome back, {user.name}", "success")
            return RedirectResponse("/dashboard", status_code=303)

    return render(request, "login.html", db, error="Invalid email or password.")


@router.get("/register")
def register_page(
    request: Request,
    role: str = Query("customer"),
    db: Session = Depends(get_db),
):
    """Show the registration form with role selection."""
    return render(request, "register.html", db, selected_role=role)


@router.post("/register")
def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    role: str = Form("customer"),
    contact: str = Form(""),
    address: str = Form(""),
    db: Session = Depends(get_db),
):
    """Register a new user account (Customer or Supplier)."""
    if password != confirm_password:
        return render(request, "register.html", db, error="Passwords do not match.", selected_role=role)

    if len(password) < 6:
        return render(request, "register.html", db, error="Password must be at least 6 characters.", selected_role=role)

    existing = db.query(User).filter(User.email == email.strip()).first()
    if existing:
        return render(request, "register.html", db, error="An account with this email already exists.", selected_role=role)

    user_role = "supplier" if role == "supplier" else "customer"

    new_user = User(
        name=name.strip(),
        email=email.strip(),
        password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
        contact=contact.strip(),
        address=address.strip(),
        role=user_role,
        is_admin=False,
    )
    db.add(new_user)
    db.commit()

    flash(request, "Account created successfully! Please sign in with your credentials.", "success")
    return RedirectResponse(f"/login?role={user_role}", status_code=303)


@router.get("/logout")
def logout(request: Request):
    """Clear session data and redirect to login."""
    request.session.clear()
    flash(request, "You have been logged out securely.", "info")
    return RedirectResponse("/login", status_code=303)
