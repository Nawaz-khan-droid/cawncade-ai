"""
CAWNCADE AI v3.5 — End-to-End Integration & Runtime Verification Test Suite.
Tests ContextLens, VisualLens (Vision + OCR), YouTube (Transcript Fallback), and Agent Chat (Evidence Assistant Mode).
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

# Add backend directory to sys.path and load environment variables
backend_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, backend_dir)
load_dotenv(os.path.join(backend_dir, ".env"))

from app.core.orchestrator import orchestrator
from app.services.agent_service import cawncade_chat_agent, cawncade_agent
from app.services.tier4 import tier4_verification_service


async def run_end_to_end_audit():
    print("=== CAWNCADE AI v3.5 END-TO-END INTEGRATION AUDIT ===")

    # 1. Test ContextLens Text Claim Analysis
    print("\n[TEST 1] ContextLens Text Claim Analysis...")
    claim_res = await orchestrator.process(
        input_text="NVIDIA announced Blackwell supercomputing architecture in 2025",
        input_type="text"
    )
    print("ContextLens Result Status:", claim_res.get("status"))
    print("Active Model Telemetry:", claim_res.get("system_metadata"))
    assert claim_res.get("status") in ("completed", "debunked", "no_sources")

    # 2. Test VisualLens Image Forensics (Synthetic Base64 image payload)
    print("\n[TEST 2] VisualLens Image Forensics (OCR + Vision Model)...")
    # Tiny 1x1 GIF base64 string
    sample_b64 = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    img_res = await orchestrator.process_image(
        image_base64=sample_b64,
        user_query="Is this image authentic?"
    )
    print("VisualLens Result Status:", img_res.get("status"))
    print("Extraction Meta:", img_res.get("metadata", {}).get("extraction"))
    assert img_res.get("status") in ("completed", "no_sources")

    # 3. Test YouTube Transcript Fallback Path
    print("\n[TEST 3] YouTube Pipeline Handling (Invalid/No Transcript URL)...")
    yt_res = await orchestrator.process(
        input_text="https://www.youtube.com/watch?v=invalid_id_test_999",
        input_type="youtube"
    )
    print("YouTube Result Status:", yt_res.get("status"))
    print("YouTube Extraction Meta:", yt_res.get("metadata", {}).get("extraction"))
    assert yt_res.get("status") in ("completed", "no_sources")

    # 4. Test Agent Chat LLM Path & Evidence Assistant Fallback Mode
    print("\n[TEST 4] Agent Chat Mode Handling...")
    chat_res = await cawncade_chat_agent.chat(user_input="What is CAWNCADE AI?")
    print("Agent Chat Output Preview:", chat_res.get("output", "")[:200].encode("ascii", errors="ignore").decode("ascii"))
    assert "output" in chat_res

    # 5. Test Forced No-LLM Tier 4 Verification Engine
    print("\n[TEST 5] Forced Tier 4 Grounded Verification Package Engine...")
    t4_report = tier4_verification_service.generate_report(
        query="NASA announced Mars landing in 2035",
        evidence_text="NASA Administrator discussed potential crewed Mars missions targeting the late 2030s decade.",
        sources_count=3
    )
    print("Tier 4 Report Preview:\n", t4_report.encode("ascii", errors="ignore").decode("ascii"))
    assert "Local Computational Evidence Verification (Tier 4 No-LLM Mode)" in t4_report

    print("\n[SUCCESS] ALL 5 END-TO-END INTEGRATION AUDIT TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    asyncio.run(run_end_to_end_audit())
