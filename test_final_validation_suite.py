import asyncio
import sys

sys.path.insert(0, 'backend')
from app.services.tier4.verification_service import tier4_verification_service
from app.services.youtube_service import fetch_transcript_scraper
from app.services.news_service import tiered_search
from app.services.tier4.entity_resolver import entity_resolver

async def run_validation_suite():
    print("=================== FINAL AUDIT VALIDATION SUITE ===================")

    # 1. Probabilistic Entity Resolver Check
    print("\n1. Probabilistic Entity Resolution Check:")
    res_x = entity_resolver.resolve_entities("vaccine X reduced deaths by 40%")
    print(f"   Input: '{res_x['input']}'")
    print(f"   Candidate Matches with Probabilistic Confidence:")
    for cand in res_x["candidates"]:
        print(f"     - Entity: {cand['entity']} (Confidence: {cand['confidence']:.2f})")
    print(f"   High Confidence Included Entities (>= 0.70): {res_x['high_confidence_entities']}")

    # 2. Test Case 1: True Space Science Claim
    print("\n2. Test Case 1: True Science Claim ('NASA launched Europa Clipper in October 2024')")
    tc1_search = await tiered_search(["NASA launched Europa Clipper in October 2024"])
    tc1_sources = tc1_search.get("sources", [])
    tc1_evidence = "\n".join([f"{s.get('title', '')}: {s.get('snippet', '')}" for s in tc1_sources[:5]])
    tc1_report = tier4_verification_service.generate_report("NASA launched Europa Clipper in October 2024", tc1_evidence, sources_count=len(tc1_sources))
    print(f"   Report Extracted (First 250 chars):\n   {tc1_report[:250]}...")

    # 3. Test Case 2: False Science Claim
    print("\n3. Test Case 2: False Science Claim ('NASA discovered life on Europa in 2025')")
    tc2_search = await tiered_search(["NASA discovered life on Europa in 2025"])
    tc2_sources = tc2_search.get("sources", [])
    tc2_evidence = "\n".join([f"{s.get('title', '')}: {s.get('snippet', '')}" for s in tc2_sources[:5]])
    tc2_report = tier4_verification_service.generate_report("NASA discovered life on Europa in 2025", tc2_evidence, sources_count=len(tc2_sources))
    print(f"   Report Extracted (First 250 chars):\n   {tc2_report[:250]}...")

    # 4. Test Case 3: Ambiguous Claim (0 Evidence Hit)
    print("\n4. Test Case 3: Ambiguous Claim ('A vaccine reduced deaths by 40%')")
    tc3_report = tier4_verification_service.generate_report("A vaccine reduced deaths by 40%", "", sources_count=0)
    print(f"   Report Extracted:\n   {tc3_report}")

    # 5. Test Case 4: YouTube Dual-Stream Subtitle Extraction (Rickroll Video ID dQw4w9WgXcQ)
    print("\n5. Test Case 4: YouTube Subtitle Extraction (dQw4w9WgXcQ):")
    yt_transcript = await fetch_transcript_scraper("dQw4w9WgXcQ")
    if yt_transcript.get("success"):
        print("   ✅ YouTube Transcript Scraper Status: SUCCESS")
        print(f"   First 120 chars extracted: '{yt_transcript.get('transcript', '')[:120]}...'")
    else:
        print(f"   ⚠️ YouTube Transcript Error: {yt_transcript.get('error')}")

if __name__ == "__main__":
    asyncio.run(run_validation_suite())
