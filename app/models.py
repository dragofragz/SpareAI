"""
SQLAlchemy ORM models for SpareAI.

Tables:
  User, Vehicle, Fault, Supplier, SparePart, PartCompatibility,
  RepairCase, Workshop, Order, OrderItem

Relationships follow the ER diagram:
  User 1:N Vehicle 1:N Fault
  Supplier 1:N SparePart 1:N PartCompatibility
  SparePart 1:N RepairCase
  User 1:N Order 1:N OrderItem N:1 SparePart
  Workshop 1:N Order (optional delivery destination)
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, LargeBinary, Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ---------------------------------------------------------------------------
# User & Vehicle
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    contact = Column(String(20), default="")
    address = Column(Text, default="")
    role = Column(String(20), default="customer")       # "customer", "supplier", "admin"
    is_admin = Column(Boolean, default=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"), nullable=True)

    vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    supplier = relationship("Supplier", back_populates="user", uselist=False)


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    type = Column(String(10), nullable=False)          # "car" or "bike"
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    vin = Column(String(30), default="")

    owner = relationship("User", back_populates="vehicles")
    faults = relationship("Fault", back_populates="vehicle", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Fault (linked to a vehicle)
# ---------------------------------------------------------------------------

class Fault(Base):
    __tablename__ = "faults"

    fault_id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id"), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="faults")


# ---------------------------------------------------------------------------
# Supplier & Spare Parts
# ---------------------------------------------------------------------------

class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    address = Column(Text, default="")
    contact = Column(String(20), default="")

    parts = relationship("SparePart", back_populates="supplier")
    user = relationship("User", back_populates="supplier", uselist=False)


class SparePart(Base):
    __tablename__ = "spare_parts"

    part_id = Column(Integer, primary_key=True, index=True)
    part_name = Column(String(150), nullable=False)
    oem_code = Column(String(50), default="")
    price = Column(Float, nullable=False)
    category = Column(String(50), default="")
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"), nullable=True)
    stock_qty = Column(Integer, default=0)
    image_url = Column(String(300), nullable=True)
    video_id = Column(String(20), nullable=True)          # YouTube video ID
    difficulty = Column(String(10), default="Medium")       # Easy | Medium | Hard
    tools_required = Column(Text, default="")

    supplier = relationship("Supplier", back_populates="parts")
    compatibilities = relationship(
        "PartCompatibility", back_populates="part", cascade="all, delete-orphan"
    )
    repair_cases = relationship("RepairCase", back_populates="solution_part")


class PartCompatibility(Base):
    """Which vehicles a part fits."""
    __tablename__ = "part_compatibilities"

    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("spare_parts.part_id"), nullable=False)
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year_from = Column(Integer, nullable=False)
    year_to = Column(Integer, nullable=False)

    part = relationship("SparePart", back_populates="compatibilities")


# ---------------------------------------------------------------------------
# RepairCase (the CBR case base)
# ---------------------------------------------------------------------------

class RepairCase(Base):
    """
    Historical repair case used by the CBR engine.
    Each case stores a symptom description, the vehicle context,
    the solution part, and a pre-computed SBERT embedding (BLOB).
    """
    __tablename__ = "repair_cases"

    case_id = Column(Integer, primary_key=True, index=True)
    symptoms = Column(Text, nullable=False)
    vehicle_type = Column(String(10), nullable=False)       # "car" or "bike"
    make = Column(String(50), nullable=True)
    model = Column(String(50), nullable=True)
    solution_part_id = Column(Integer, ForeignKey("spare_parts.part_id"), nullable=False)
    embedding = Column(LargeBinary, nullable=True)          # float32 numpy array as bytes

    solution_part = relationship("SparePart", back_populates="repair_cases")


# ---------------------------------------------------------------------------
# Workshop
# ---------------------------------------------------------------------------

class Workshop(Base):
    __tablename__ = "workshops"

    workshop_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    address = Column(Text, default="")
    contact = Column(String(20), default="")
    verified = Column(Boolean, default=False)
    rating = Column(Float, default=0.0)

    orders = relationship("Order", back_populates="workshop")


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    workshop_id = Column(Integer, ForeignKey("workshops.workshop_id"), nullable=True)
    status = Column(String(20), default="Placed")           # Placed -> Confirmed -> Shipped -> Delivered
    total = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    workshop = relationship("Workshop", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    part_id = Column(Integer, ForeignKey("spare_parts.part_id"), nullable=False)
    qty = Column(Integer, default=1)
    price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    part = relationship("SparePart")
