"""
evaluate.py — Leave-One-Out Cross-Validation for SpareAI CBR Engine.

Simulates real-world performance by iterating through all historical repair cases:
  1. Removes case i from the case base.
  2. Uses case i's symptom description as the query.
  3. Evaluates if the true solution part appears in Top-1 and Top-3 recommendations.
  4. Computes Top-1 Accuracy and Top-3 Accuracy (Overall, Cars, and Bikes).

Use the output metrics directly in your final year project presentation and report.
"""

import sys
import os
import numpy as np

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import RepairCase, SparePart


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))


def evaluate_leave_one_out():
    db = SessionLocal()
    try:
        cases = db.query(RepairCase).all()
        total_cases = len(cases)
        if total_cases == 0:
            print("[Error] No repair cases found in database. Run `python seed.py` first.")
            return

        print("=" * 65)
        print(" SpareAI CBR Recommendation Engine — Leave-One-Out Evaluation")
        print(f" Benchmark Case Base: {total_cases} Historical Repairs")
        print(" Model: Sentence-BERT (all-MiniLM-L6-v2) | k = 5 nearest neighbors")
        print("=" * 65)

        correct_top1 = 0
        correct_top3 = 0

        # Stats by vehicle type
        by_type = {
            "car": {"total": 0, "top1": 0, "top3": 0},
            "bike": {"total": 0, "top1": 0, "top3": 0},
        }

        # Pre-decode embeddings
        case_records = []
        for c in cases:
            emb = np.frombuffer(c.embedding, dtype=np.float32)
            case_records.append({
                "id": c.case_id,
                "symptoms": c.symptoms,
                "vehicle_type": c.vehicle_type,
                "make": c.make,
                "model": c.model,
                "target_part_id": c.solution_part_id,
                "embedding": emb,
            })

        for i, test_case in enumerate(case_records):
            vtype = test_case["vehicle_type"]
            query_emb = test_case["embedding"]
            target_pid = test_case["target_part_id"]

            # Filter candidates: same vehicle_type, exclude self
            scored = []
            for j, candidate in enumerate(case_records):
                if i == j:
                    continue  # Leave-one-out
                if candidate["vehicle_type"] != vtype:
                    continue

                sim = cosine_sim(query_emb, candidate["embedding"])

                # Make/Model boost matching CBR pipeline
                if test_case["make"] and candidate["make"] and test_case["make"].lower() == candidate["make"].lower():
                    sim = min(sim + 0.03, 1.0)
                if test_case["model"] and candidate["model"] and test_case["model"].lower() == candidate["model"].lower():
                    sim = min(sim + 0.05, 1.0)

                scored.append((candidate["target_part_id"], sim))

            if not scored:
                continue

            scored.sort(key=lambda x: x[1], reverse=True)
            top_k = scored[:5]

            # Weighted voting by solution part
            part_votes = {}
            for pid, sim in top_k:
                if pid not in part_votes:
                    part_votes[pid] = 0.0
                part_votes[pid] += sim

            ranked_parts = sorted(part_votes.items(), key=lambda x: x[1], reverse=True)
            top_part_ids = [p[0] for p in ranked_parts[:3]]

            # Accuracy checks
            is_top1 = len(top_part_ids) > 0 and top_part_ids[0] == target_pid
            is_top3 = target_pid in top_part_ids

            if is_top1:
                correct_top1 += 1
            if is_top3:
                correct_top3 += 1

            if vtype in by_type:
                by_type[vtype]["total"] += 1
                if is_top1:
                    by_type[vtype]["top1"] += 1
                if is_top3:
                    by_type[vtype]["top3"] += 1

        top1_pct = (correct_top1 / total_cases) * 100
        top3_pct = (correct_top3 / total_cases) * 100

        print("\nEvaluation Results:")
        print("-" * 65)
        print(f"  Overall Total Cases Evaluated : {total_cases}")
        print(f"  Top-1 Recommendation Accuracy : {top1_pct:.2f}% ({correct_top1}/{total_cases})")
        print(f"  Top-3 Recommendation Accuracy : {top3_pct:.2f}% ({correct_top3}/{total_cases})")
        print("-" * 65)

        for vt, stats in by_type.items():
            t = stats["total"]
            if t > 0:
                t1 = (stats["top1"] / t) * 100
                t3 = (stats["top3"] / t) * 100
                print(f"  Category: {vt.upper():<5} ({t} cases) | Top-1: {t1:6.2f}% | Top-3: {t3:6.2f}%")

        print("=" * 65)
        print("Presentation Quote:")
        print(f'  "Our SBERT-CBR engine achieved {top1_pct:.1f}% Top-1 and {top3_pct:.1f}% Top-3 accuracy')
        print(f'   across {total_cases} cross-validated repair cases with semantic symptom matching."')
        print("=" * 65)

    finally:
        db.close()


if __name__ == "__main__":
    evaluate_leave_one_out()
