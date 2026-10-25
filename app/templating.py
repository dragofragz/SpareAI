"""
Centralised template-rendering helper.

Every route calls ``render(request, "template.html", db, key=value, ...)``
which automatically injects the common context variables every template needs:

- **user** – the currently logged-in ``User`` object (or ``None``)
- **messages** – flash messages accumulated during the request
- **cart_count** – number of distinct items in the session cart
"""

from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.models import User

templates = Jinja2Templates(directory="app/templates")


def render(request: Request, template_name: str, db: Session = None, **kwargs):
    """Return a ``TemplateResponse`` with common context injected."""

    # Current user from session
    user_id = request.session.get("user_id")
    user = None
    if user_id and db:
        user = db.query(User).filter(User.user_id == user_id).first()

    # Flash messages (consumed on read)
    messages = request.session.pop("_messages", [])

    # Cart badge count
    cart = request.session.get("cart", [])

    context = {
        "request": request,
        "user": user,
        "messages": messages,
        "cart_count": len(cart),
    }
    context.update(kwargs)
    return templates.TemplateResponse(request=request, name=template_name, context=context)
