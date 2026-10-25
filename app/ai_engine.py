"""
AI Recommendation Engine — Sentence-BERT + Case-Based Reasoning (CBR).

Architecture (based on Schiavo et al., IEEE Access 2024):

  1. ENCODE   — The user's fault description is encoded into a 384-dim vector
                using Sentence-BERT (all-MiniLM-L6-v2).
  2. RETRIEVE — Cosine similarity is computed against all historical RepairCase
                embeddings that share the same vehicle_type.  Similarity is
                boosted (+0.03 make, +0.05 model) when domain context matches.
  3. RANK     — The top-k most similar cases are aggregated by solution part
                using similarity-weighted voting.  Confidence is derived from
                the best-matching case's similarity plus a consensus bonus.
  4. CHECK    — Each recommended part is checked for compatibility with the
                user's vehicle (make, model, year) and for stock across
                all suppliers.

The model is loaded once at startup and cached globally for fast inference.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from app.models import RepairCase, SparePart, PartCompatibility, Supplier

# ---------------------------------------------------------------------------
# Global model cache
# ---------------------------------------------------------------------------
_model: SentenceTransformer | None = None


def load_model() -> SentenceTransformer:
    """Load the Sentence-BERT model lazily and cache it globally with low memory footprint."""
    global _model
    if _model is None:
        try:
            import torch
            torch.set_num_threads(1)
        except Exception:
            pass

        try:
            _model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
        except Exception:
            _model = SentenceTransformer("all-MiniLM-L6-v2")

        try:
            _model.eval()
        except Exception:
            pass
    return _model


def encode_text(text: str) -> np.ndarray:
    """Encode *text* into a normalised 384-dim float32 embedding."""
    model = load_model()
    try:
        import torch
        with torch.no_grad():
            return model.encode(text, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
    except Exception:
        return model.encode(text, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Dot product of two L2-normalised vectors = cosine similarity."""
    return float(np.dot(a, b))


def get_service_guidance(part: SparePart, confidence: float = 75.0) -> dict:
    """
    Determine whether the repair is a safe DIY task or requires a professional workshop technician.
    Considers part difficulty, tool requirements, safety risks, and AI confidence.
    """
    diff = (part.difficulty or "Medium").capitalize()

    if confidence < 40.0:
        return {
            "verdict": "technician_required",
            "is_diy": False,
            "badge_label": "Professional Technician Required",
            "badge_color": "red",
            "title": "Professional Workshop Inspection Recommended",
            "summary": "Because the symptom pattern is complex or diagnostic confidence is low, physical inspection using professional workshop scanners and vehicle lifts is advised before replacing parts.",
            "estimated_time": "1 - 2 hours at certified workshop",
            "safety_warning": "High risk of misdiagnosis. Consult an expert technician.",
            "recommendation": "Book Service at Nearby Workshop",
        }

    if diff == "Easy":
        return {
            "verdict": "diy_friendly",
            "is_diy": True,
            "badge_label": "Safe DIY — You Can Do This Yourself",
            "badge_color": "green",
            "title": "You Can Do This Yourself at Home",
            "summary": "This component replacement is straightforward and safe for vehicle owners. It requires only basic hand tools, carries minimal safety hazard, and can be completed in your garage or driveway.",
            "estimated_time": "15 - 30 minutes",
            "safety_warning": "Ensure engine is cold and ignition is switched off before servicing.",
            "recommendation": "Perform DIY Installation with Tutorial Video",
        }
    elif diff == "Medium":
        return {
            "verdict": "diy_caution",
            "is_diy": True,
            "badge_label": "Moderate DIY — Tools & Caution Advised",
            "badge_color": "amber",
            "title": "Feasible DIY with Proper Tools & Mechanical Caution",
            "summary": "Can be performed at home if you have intermediate mechanical confidence, socket wrenches, and rated jack stands. If you do not have safe vehicle lifting gear, professional installation is recommended.",
            "estimated_time": "45 - 90 minutes",
            "safety_warning": "Never get underneath a vehicle supported only by a hydraulic jack. Always use certified jack stands.",
            "recommendation": "Follow Video Tutorial Carefully or Ship to Workshop",
        }
    else:  # Hard
        return {
            "verdict": "technician_required",
            "is_diy": False,
            "badge_label": "High Complexity — Certified Technician Required",
            "badge_color": "red",
            "title": "Professional Workshop Installation Required",
            "summary": "This is a safety-critical structural or mechanical component (suspension geometry, internal clutch, or drivetrain). Proper torque sequencing, pressing ball joints, and wheel alignment calibration are strictly required.",
            "estimated_time": "2 - 4 hours (Workshop Bay)",
            "safety_warning": "Critical Safety Component: Incorrect DIY torque or fitment can lead to loss of vehicle steering control or severe drivetrain failure.",
            "recommendation": "Order Part & Choose 'Deliver to Workshop' for Professional Fitting",
        }


def _stock_info_for_part(db: Session, part: SparePart) -> list[dict]:
    """Return stock levels for *part* across every supplier that carries it."""
    same_name_parts = (
        db.query(SparePart)
        .filter(SparePart.part_name == part.part_name)
        .all()
    )
    seen, info = set(), []
    for p in same_name_parts:
        if p.supplier_id and p.supplier_id not in seen:
            sup = db.query(Supplier).filter(Supplier.supplier_id == p.supplier_id).first()
            if sup:
                info.append({
                    "supplier_name": sup.name,
                    "supplier_id": sup.supplier_id,
                    "qty": p.stock_qty,
                    "part_id": p.part_id,
                    "lat": sup.lat,
                    "lng": sup.lng,
                    "contact": sup.contact,
                    "address": sup.address,
                })
                seen.add(p.supplier_id)
    return info


# ---------------------------------------------------------------------------
# Main recommendation pipeline
# ---------------------------------------------------------------------------

def recommend_parts(
    db: Session,
    fault_description: str,
    vehicle_type: str,
    make: str | None = None,
    model: str | None = None,
    year: int | None = None,
    top_k: int = 5,
    top_n: int = 3,
    threshold: float = 0.40,
) -> list[dict]:
    """
    Recommend spare parts for a fault description.

    Returns a list (length <= *top_n*) of dicts:
        {
            "part":            SparePart ORM object,
            "confidence":      float  (0-100),
            "similar_cases":   list[{symptoms, similarity, make, model}],
            "compatible":      bool | None,
            "stock_info":      list[dict],
            "low_confidence":  bool,
        }
    """
    # --- Step 1: encode query ---------------------------------------------------
    query_emb = encode_text(fault_description)

    # --- Step 2: retrieve cases matching vehicle_type ---------------------------
    cases = (
        db.query(RepairCase)
        .filter(RepairCase.vehicle_type == vehicle_type)
        .all()
    )
    if not cases:
        return []

    # --- Step 3 & 4: score each case (cosine sim + domain boost) ----------------
    scored: list[tuple[RepairCase, float]] = []
    for case in cases:
        if case.embedding is None:
            continue
        case_emb = np.frombuffer(case.embedding, dtype=np.float32)
        sim = _cosine_sim(query_emb, case_emb)

        # CBR domain-specific boost when make / model matches the query vehicle
        if make and case.make and case.make.lower() == make.lower():
            sim = min(sim + 0.03, 1.0)
        if model and case.model and case.model.lower() == model.lower():
            sim = min(sim + 0.05, 1.0)

        scored.append((case, sim))

    if not scored:
        return []

    scored.sort(key=lambda x: x[1], reverse=True)
    top_cases = scored[:top_k]

    # --- Step 5: aggregate by solution part (similarity-weighted voting) ---------
    part_agg: dict[int, dict] = {}
    for case, sim in top_cases:
        pid = case.solution_part_id
        if pid not in part_agg:
            part_agg[pid] = {"max_sim": 0.0, "count": 0, "cases": []}
        bucket = part_agg[pid]
        bucket["max_sim"] = max(bucket["max_sim"], sim)
        bucket["count"] += 1
        bucket["cases"].append({
            "symptoms": case.symptoms,
            "similarity": round(sim * 100, 1),
            "make": case.make,
            "model": case.model,
        })

    # --- Step 6: build result dicts ---------------------------------------------
    results: list[dict] = []
    for pid, agg in part_agg.items():
        # Confidence = best case similarity + small consensus bonus
        confidence = agg["max_sim"] * 100
        consensus_bonus = min(3.0 * (agg["count"] - 1), 10.0)
        confidence = min(confidence + consensus_bonus, 99.9)

        part = db.query(SparePart).filter(SparePart.part_id == pid).first()
        if part is None:
            continue

        # Compatibility check against the user's vehicle
        compatible = None
        if make and model and year:
            compat = (
                db.query(PartCompatibility)
                .filter(
                    PartCompatibility.part_id == pid,
                    PartCompatibility.make.ilike(make),
                    PartCompatibility.model.ilike(model),
                    PartCompatibility.year_from <= year,
                    PartCompatibility.year_to >= year,
                )
                .first()
            )
            compatible = compat is not None

        # Stock across all suppliers
        stock = _stock_info_for_part(db, part)

        # AI assessment: whether customer needs a professional technician or can DIY
        service_guidance = get_service_guidance(part, confidence)

        results.append({
            "part": part,
            "confidence": round(confidence, 1),
            "similar_cases": sorted(
                agg["cases"], key=lambda c: c["similarity"], reverse=True
            )[:3],
            "compatible": compatible,
            "stock_info": stock,
            "low_confidence": confidence < (threshold * 100),
            "service_guidance": service_guidance,
        })

    results.sort(key=lambda r: r["confidence"], reverse=True)
    return results[:top_n]
