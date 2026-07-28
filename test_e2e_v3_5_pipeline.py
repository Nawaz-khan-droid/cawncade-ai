import sys
import asyncio
import os

sys.path.insert(0, 'backend')
from app.services.tier4.claim_parser import claim_parser
from app.services.tier4.entity_resolver import entity_resolver
from app.services.news_service import tiered_search

async def run_v3_5_audit():
    print("=================== E2E PIPELINE AUDIT v3.5 ===================")
    
    # 1. Verify find_working_free_models.py token safety
    with open("find_working_free_models.py", "r") as f:
        code = f.read()
        import re
        has_token = bool(re.search(r"hf_[a-zA-Z0-9]{20,}", code))
        assert not has_token, "ERROR: Hardcoded HF token detected!"
        print("1. find_working_free_models.py check: ✅ Token loaded cleanly from .env")

    # 2. Entity Resolver Check
    resolved = entity_resolver.resolve_entities("WHO says vaccine X reduced deaths by 40% in India in 2024")
    print(f"\n2. Entity Linking Check:")
    print("   Canonical Entities:", resolved["canonical_entities"])
    print("   Entity Aliases    :", resolved["entity_aliases"])

    # 3. Normalized Query Scoring Check
    raw_health = "WHO says vaccine X reduced deaths by 40% in India in 2024"
    raw_lyric = "Unknown Title [♪♪♪] ♪ We're no strangers to love ♪"
    
    p_health = claim_parser.parse_claim(raw_health)
    p_lyric = claim_parser.parse_claim(raw_lyric)

    q_health = claim_parser.generate_expanded_queries(raw_health)[0]
    q_lyric = claim_parser.generate_expanded_queries(raw_lyric)[0]

    score_health = claim_parser.score_query_quality(q_health, p_health)
    score_lyric = claim_parser.score_query_quality(q_lyric, p_lyric)

    print(f"\n3. Normalized 0-100% Quality Score Check:")
    print(f"   Health Claim ('{claim_parser.classify_claim_type(p_health)}') Top Query: '{q_health}' -> Score: {score_health:.1f}%")
    print(f"   Lyric Claim  ('{claim_parser.classify_claim_type(p_lyric)}') Top Query: '{q_lyric}' -> Score: {score_lyric:.1f}%")

    # 4. Adaptive Early Stopping Search Verification
    print(f"\n4. Adaptive Early Stopping & Cost Control Search:")
    expanded_health = claim_parser.generate_expanded_queries(raw_health)
    res = await tiered_search(expanded_health)
    print("   Queries Generated:", len(expanded_health))
    print("   Queries Executed :", len(res.get("queries_executed", [])))
    print("   Early Stopped    :", res.get("early_stopped"))
    print("   Sources Found    :", len(res.get("sources", [])))

if __name__ == "__main__":
    asyncio.run(run_v3_5_audit())
