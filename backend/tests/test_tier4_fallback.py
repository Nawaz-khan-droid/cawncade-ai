import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.offline_nlp_service import offline_nlp_service


def test_tier4_nlp_summary():
    sample_evidence = (
        "NVIDIA Corporation announced a new supercomputing platform in Santa Clara on Dec 15, 2025. "
        "CEO Jensen Huang demonstrated the Blackwell architecture to industry analysts. "
        "The technology aims to reduce energy consumption in large-scale data centers by 45 percent. "
        "Microsoft Corporation expressed interest in deploying the processors by late 2026."
    )

    # 1. Test offline report generation
    report = offline_nlp_service.generate_report(sample_evidence, sources_count=4)
    print("--- Tier 4 Report Preview ---")
    print(report.encode("ascii", errors="ignore").decode("ascii"))
    print("-----------------------------")

    assert "Local Computational Evidence Analysis (Tier 4 Offline Mode)" in report
    assert "Key Extracted Sentences:" in report
    assert "Detected Grounded Entities:" in report

    # 2. Test Entity Extractor directly
    entities = offline_nlp_service.extract_entities(sample_evidence)
    print("Extracted Entities:", entities)
    assert isinstance(entities, dict)
    assert "dates" in entities
    assert "organizations" in entities

    # 3. Test Empty Evidence Edge Case
    empty_report = offline_nlp_service.generate_report("", sources_count=0)
    assert "Tier 4 Offline Analysis Unavailable" in empty_report

    print("\nSUCCESS: Tier 4 Offline No-LLM Fallback operates cleanly on CPU!")


if __name__ == "__main__":
    test_tier4_nlp_summary()
