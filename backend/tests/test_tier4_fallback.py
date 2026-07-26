import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.tier4 import tier4_verification_service
from app.services.tier4.claim_parser import claim_parser
from app.services.tier4.evidence_ranker import evidence_ranker
from app.services.tier4.entity_matcher import entity_matcher
from app.services.tier4.verdict_engine import verdict_engine


def test_tier4_modular_verification():
    claim = "NVIDIA announced Blackwell supercomputing architecture in 2025"
    sample_evidence = (
        "NVIDIA Corporation announced a new supercomputing platform in Santa Clara on Dec 15, 2025. "
        "CEO Jensen Huang demonstrated the Blackwell architecture to industry analysts. "
        "The technology aims to reduce energy consumption in large-scale data centers by 45 percent. "
        "Microsoft Corporation expressed interest in deploying the processors by late 2026."
    )

    # 1. Test Claim Parser
    parsed_claim = claim_parser.parse_claim(claim)
    print("Parsed Claim:", parsed_claim)
    assert "2025" in parsed_claim["years"]

    # 2. Test Hybrid Evidence Ranker (BM25 + MiniLM)
    sentences = [s.strip() for s in sample_evidence.split(".") if len(s.strip()) > 15]
    ranked = evidence_ranker.rank_evidence(claim, sentences, top_k=2)
    print("\nHybrid BM25 + MiniLM Ranked Evidence:", ranked)
    assert len(ranked) > 0
    assert "hybrid_score" in ranked[0]

    # 3. Test Full Tier 4 Report Generation
    report = tier4_verification_service.generate_report(claim, sample_evidence, sources_count=4)
    print("\n--- Modular Tier 4 Verification Report Preview ---")
    print(report.encode("ascii", errors="ignore").decode("ascii"))
    print("--------------------------------------------------")

    assert "Local Computational Evidence Verification (Tier 4 No-LLM Mode)" in report
    assert "Grounded Deterministic Verdict" in report
    assert "Hybrid BM25 + MiniLM Ranked Evidence Sentences:" in report

    # 4. Test Date Conflict Verdict Engine
    conflict_claim = "NVIDIA announced Blackwell supercomputing architecture in 2018"
    conflict_parsed = claim_parser.parse_claim(conflict_claim)
    evidence_parsed = claim_parser.parse_claim(sample_evidence)
    match_stats = entity_matcher.compare_entities(conflict_parsed, evidence_parsed)
    conflict_verdict = verdict_engine.calculate_verdict(match_stats, sources_count=4, evidence_length=len(sample_evidence))
    print("\nDate Conflict Verdict Engine Output:", conflict_verdict)
    assert conflict_verdict["year_conflict"] is True

    print("\nSUCCESS: Tier 4 Modular Grounded Verification Engine operates cleanly on CPU!")


if __name__ == "__main__":
    test_tier4_modular_verification()
