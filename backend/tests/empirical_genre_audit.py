import asyncio
import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath("."))

from app.core.orchestrator import orchestrator

TEST_CLAIMS = [
    {"genre": "Politics/News", "claim": "Narendra Modi inaugurated the Chenab Rail Bridge in Kashmir"},
    {"genre": "Health/Medical", "claim": "Drinking hot lemon water cures COVID-19 and cancer"},
    {"genre": "Science/Space", "claim": "NASA James Webb Telescope detected atmospheric water vapor on exoplanet K2-18b"},
    {"genre": "Entertainment", "claim": "Taylor Swift became a billionaire following The Eras Tour"},
    {"genre": "Finance/Crypto", "claim": "Bitcoin reached a new all-time high above 100,000 dollars"},
    {"genre": "Tech/AI", "claim": "OpenAI released GPT-4o with real-time voice and vision capabilities"}
]

async def run_audit():
    print("==================================================================")
    print("         CAWNCADE AI v3.5 — MULTI-GENRE EMPIRICAL AUDIT          ")
    print("==================================================================")
    
    # Reset circuit breakers & flush local cache/FAISS index to force clean live pipeline execution
    from app.core.resilience import reset_all_circuits
    reset_all_circuits()
    
    from app.services.dictionary_matcher import dictionary_matcher
    from app.services.cache_service import semantic_cache, INDEX_FILE, METADATA_FILE
    
    dictionary_matcher.claims_lookup = {}
    if os.path.exists(dictionary_matcher.storage_path):
        try:
            with open(dictionary_matcher.storage_path, "w", encoding="utf-8") as f:
                json.dump({}, f)
        except Exception:
            pass

    import faiss
    semantic_cache.index = faiss.IndexFlatIP(384)
    semantic_cache.cached_claims = []
    semantic_cache.cached_verdicts = []
    for fpath in (INDEX_FILE, METADATA_FILE):
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception:
                pass

    results = []
    
    for idx, item in enumerate(TEST_CLAIMS, 1):
        genre = item["genre"]
        claim = item["claim"]
        print(f"\n[{idx}/{len(TEST_CLAIMS)}] Testing Genre: [{genre}]")
        print(f"    Claim: '{claim}'")
        
        t0 = time.time()
        try:
            res = await orchestrator.process(input_text=claim, input_type="text")
            elapsed = int((time.time() - t0) * 1000)
            
            verdict = res.get("verdict") or res.get("explainability", {}).get("verdict") or res.get("metadata", {}).get("fact_verdict", {}).get("verdict", "UNVERIFIED")
            confidence = res.get("confidence", 0.0)
            sources = res.get("sources_cited", [])
            trusted = res.get("metadata", {}).get("trusted_domains_found", [])
            deep_dive = res.get("agent_deep_dive", "")
            llm_tier = res.get("system_metadata", {}).get("llm_tier", "N/A")
            
            has_min_conf = confidence >= 0.40
            has_sources = len(sources) >= 1
            has_coherent_summary = len(deep_dive.strip()) >= 50
            is_valid_verdict = verdict in ("VERIFIED_TRUE", "SUPPORTED BY AVAILABLE EVIDENCE", "FALSE_DEBUNKED", "CONTRADICTED BY AVAILABLE EVIDENCE", "PARTIALLY_TRUE")

            if has_min_conf and has_sources and has_coherent_summary and is_valid_verdict:
                status = "PASS"
            else:
                status = "FAIL (QUALITY)"
            
            audit_entry = {
                "genre": genre,
                "claim": claim,
                "status": status,
                "verdict": verdict,
                "confidence": confidence,
                "latency_ms": elapsed,
                "sources_count": len(sources),
                "trusted_domains": trusted,
                "llm_tier": llm_tier,
                "summary_preview": deep_dive[:200]
            }
            results.append(audit_entry)
            
            print(f"    --> Result: [{status}] | Verdict: {verdict} | Conf: {confidence:.2f} | Latency: {elapsed}ms | Sources: {len(sources)} | Trusted: {trusted}")
            print(f"    --> Summary: {deep_dive[:120]}...")
            
        except Exception as e:
            print(f"    --> ERROR: {e}")
            results.append({"genre": genre, "claim": claim, "status": "ERROR", "error": str(e)})
            
    print("\n==================================================================")
    print("                      AUDIT SUMMARY RESULTS                       ")
    print("==================================================================")
    passed_count = sum(1 for r in results if r.get("status") == "PASS")
    print(f"Total Genres Tested : {len(TEST_CLAIMS)}")
    print(f"Passed Verifications: {passed_count}/{len(TEST_CLAIMS)} ({passed_count/len(TEST_CLAIMS)*100:.1f}%)")
    print("==================================================================")
    
    with open("db/multi_genre_audit_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_audit())
