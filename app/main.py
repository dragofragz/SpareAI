"""
SpareAI — FastAPI application entry point.

Startup sequence:
  1. Create all database tables (if they don't exist).
  2. Pre-load the Sentence-BERT model so the first diagnosis is fast.
  3. Mount static files and include every router.

Run with:
    uvicorn app.main:app --reload
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

from app.database import engine, Base
from app.ai_engine import load_model


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load resources at startup."""
    Base.metadata.create_all(bind=engine)
    print("[SpareAI] Database verified — server is ready!")
    yield


# ---------------------------------------------------------------------------
# App creation
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SpareAI",
    description="AI-Based Spare Parts E-Commerce and Field Service Assistance",
    lifespan=lifespan,
)

# Cookie-based sessions (signed with itsdangerous)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SECRET_KEY", "spareai-secret-2024-cec"),
    max_age=3600 * 24,  # 24 hours
)

# Static assets
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/js", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from app.routes import (          # noqa: E402  (must come after app creation)
    auth, dashboard, diagnosis,
    parts, cart, orders,
    workshops, tutorials,
    admin, about, api, supplier,
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(diagnosis.router)
app.include_router(parts.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(workshops.router)
app.include_router(tutorials.router)
app.include_router(admin.router)
app.include_router(supplier.router)
app.include_router(about.router)
app.include_router(api.router)


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    """Redirect ``/`` to the dashboard."""
    return RedirectResponse("/dashboard", status_code=303)
