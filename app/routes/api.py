"""
JSON API routes — programmatic access to the recommendation engine.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.ai_engine import recommend_parts

router = APIRouter()


@router.get("/api/recommend")
def api_recommend(
    description: str = Query(...),
    vehicle_type: str = Query("car"),
    make: str = Query(None),
    model_name: str = Query(None, alias="model"),
    year: int = Query(None),
    db: Session = Depends(get_db),
):
    """Return AI part recommendations as JSON."""
    results = recommend_parts(
        db,
        description,
        vehicle_type,
        make,
        model_name,
        year,
    )

    return {
        "query": description,
        "vehicle_type": vehicle_type,
        "results": [
            {
                "part_name": r["part"].part_name,
                "part_id": r["part"].part_id,
                "oem_code": r["part"].oem_code,
                "price": r["part"].price,
                "confidence": r["confidence"],
                "similar_cases": r["similar_cases"],
                "compatible": r["compatible"],
                "stock_info": r["stock_info"],
                "low_confidence": r["low_confidence"],
            }
            for r in results
        ],
    }
