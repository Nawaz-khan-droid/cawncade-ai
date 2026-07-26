import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.offline_nlp_service import offline_nlp_service


def test_tier4_nlp_summary():
    claim = "NVIDIA announced Blackwell supercomputing architecture in 2025"
    sample_evidence = (
        "NVIDIA Corporation announced a new supercomputing platform in Santa Clara on Dec 15, 2025. "
        "CEO Jensen Huang demonstrated the Blackwell architecture to industry analysts. "
        "The technology aims to reduce energy consumption in large-scale data centers by 45 percent. "
        "Microsoft Corporation expressed interest in deploying the processors by late 2026."
    )

    # 1. Test offline report generation with BM25 & Grounded Verdict
    report = offline_nlp_service.generate_report(claim, sample_evidence, sources_count=4)
    print("--- Tier 4 Grounded Verification Report Preview ---")
    print(report.encode("ascii", errors="ignore").decode("ascii"))
    print("---------------------------------------------------")

    assert "Local Computational Evidence Verification (Tier 4 No-LLM Mode)" in report
    assert "Grounded Deterministic Verdict" in report
    assert "BM25 Extracted Evidence Sentences:" in report
    assert "Grounded Entities Detected:" in report

    # 2. Test Grounded Verdict Engine directly
    eval_res = offline_nlp_service.evaluate_grounded_verdict(claim, sample_evidence, sources_count=4)
    print("\nDeterministic Verdict Engine Output:", eval_res)
    assert eval_res["verdict"] in ("SUPPORTED BY AVAILABLE EVIDENCE", "MIXED / PARTIALLY SUPPORTED EVIDENCE")
    assert eval_res["date_match"] is True

    # 3. Test Date Conflict Detection
    conflict_claim = "NVIDIA announced Blackwell supercomputing architecture in 2018"
    conflict_res = offline_nlp_service.evaluate_grounded_verdict(conflict_claim, sample_evidence, sources_count=4)
    print("\nDate Conflict Verdict Engine Output:", conflict_res)
    assert conflict_res["date_conflict"] is True

    # 4. Test Empty Evidence Edge Case
    empty_report = offline_nlp_service.generate_report(claim, "", sources_count=0)
    assert "Tier 4 Computational Analysis (No-LLM Mode)" in empty_report

    print("\nSUCCESS: Tier 4 No-LLM Deterministic Verification Engine operates cleanly on CPU!")


if __name__ == "__main__":
    test_tier4_nlp_summary()
