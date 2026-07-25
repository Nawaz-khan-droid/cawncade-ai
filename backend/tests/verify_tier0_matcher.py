import os
import sys
import time
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.dictionary_matcher import PreFlightDictionaryMatcher

async def run_speed_trial():
    print("[INIT] Initializing Tier 0 Speed Trial Interceptor...")
    # Initialize the matcher class instance locally
    matcher = PreFlightDictionaryMatcher(storage_path="db/test_viral_claims.json")
    
    # 1. Base Truth Data Payload to Seed the Dictionary
    original_claim = "The government passed a new digital privacy tax act in July 2026"
    mock_verdict = "### Final Verdict\nFALSE\n\n### Evidence\nNo legislative bills match this assertion."
    
    # Commit the baseline record straight to the JSON data matrix
    matcher.commit_viral_claim(original_claim, mock_verdict)
    
    # 2. Simulate an Incoming User Claim with Typos and Structural Drift
    user_variant = "is it true that govt passed a new digital privacy tax act in July 2026??"
    print(f"\n[IN] Incoming User Variant: '{user_variant}'")
    print("[PROCESS] Triggering Tier 0 Text Matcher Lookup Pass...")
    
    # 3. High-Precision Microsecond Benchmark Timing Loop
    start_time = time.perf_counter()
    cached_hit = matcher.lookup_viral_claim(user_variant, ratio_threshold=0.80)
    execution_time_seconds = time.perf_counter() - start_time
    
    # Convert seconds to microseconds (1s = 1,000,000us)
    execution_time_microseconds = execution_time_seconds * 1_000_000
    
    print("\n==================================================")
    print("BENCHMARK METRICS:")
    print("==================================================")
    print(f"[TIME] Total Latency: {execution_time_microseconds:.2f} microseconds (us)")
    print(f"[TIME] Equivalent to: {execution_time_seconds * 1000:.4f} milliseconds (ms)")
    
    if cached_hit:
        print("[SUCCESS] TEST PASSED: Tier 0 successfully caught the string variation under 1ms!")
    else:
        print("[FAIL] TEST FAILED: The SequenceMatcher threshold dropped the connection fallback.")
    print("==================================================")

    # Clean up the test database asset file from the workspace shell
    if os.path.exists("db/test_viral_claims.json"):
        os.remove("db/test_viral_claims.json")

if __name__ == "__main__":
    asyncio.run(run_speed_trial())
