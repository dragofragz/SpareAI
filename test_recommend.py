"""
Automated tests for SpareAI recommendation engine and API endpoints.

Tests:
  1. AI Recommendation: "grinding noise from underbody over speed bumps" on a
     Hyundai i20 returns "Front Lower Control Arm Suspension Assembly" as top-1.
  2. JSON API endpoint /api/recommend returns valid status 200 and ranked parts.
  3. Bike fault recommendation: chain clanking/slipping on Royal Enfield returns
     Chain & Sprocket kit.
"""

import pytest
from app.database import SessionLocal
from app.ai_engine import recommend_parts
from app.routes.api import api_recommend


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()


def test_lower_control_arm_recommendation(db):
    """
    Core project requirement:
    Fault: 'grinding noise from underbody over speed bumps'
    Vehicle: Hyundai i20 2020 (car)
    Expected top result: Lower Control Arm with confidence >= 60% and compatible=True.
    """
    fault_desc = "grinding noise from underbody over speed bumps"
    results = recommend_parts(
        db,
        fault_description=fault_desc,
        vehicle_type="car",
        make="Hyundai",
        model="i20",
        year=2020,
    )

    assert len(results) > 0, "Expected at least one recommendation"
    top_result = results[0]
    top_part_name = top_result["part"].part_name

    assert "Lower Control Arm" in top_part_name, (
        f"Expected Lower Control Arm as top part, got: {top_part_name}"
    )
    assert top_result["confidence"] >= 60.0, (
        f"Expected confidence >= 60%, got: {top_result['confidence']}%"
    )
    assert top_result["compatible"] is True, "Expected part to be compatible with Hyundai i20 2020"


def test_bike_chain_recommendation(db):
    """
    Two-wheeler fault test:
    Fault: 'chain slipping under hard acceleration with clanking noise'
    Vehicle: Royal Enfield Classic 350 (bike)
    Expected top result: Drive Chain & Sprocket Kit.
    """
    fault_desc = "chain slipping under hard acceleration with clanking noise"
    results = recommend_parts(
        db,
        fault_description=fault_desc,
        vehicle_type="bike",
        make="Royal Enfield",
        model="Classic 350",
        year=2019,
    )

    assert len(results) > 0
    top_part = results[0]["part"].part_name
    assert "Chain & Sprocket" in top_part or "Chain" in top_part, (
        f"Expected Chain & Sprocket kit, got: {top_part}"
    )


def test_api_recommend_endpoint(db):
    """
    Test the programmatic REST API /api/recommend returns structured JSON.
    """
    data = api_recommend(
        description="Loud grinding noise from underbody when turning over speed bumps",
        vehicle_type="car",
        make="Hyundai",
        model_name="i20",
        year=2020,
        db=db,
    )
    assert "results" in data
    assert len(data["results"]) > 0

    top = data["results"][0]
    assert "Lower Control Arm" in top["part_name"]
    assert top["confidence"] > 50
    assert "similar_cases" in top
    assert len(top["similar_cases"]) > 0
