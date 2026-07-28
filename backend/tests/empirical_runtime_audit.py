"""
Empirical Runtime Audit & Instrumentation Diagnostic
Captures exact HTTP status codes, request URLs, response bodies, input classification traces,
query generation, retrieval outputs, BM25/MiniLM scores, trust decisions, and verdict steps.
"""

import sys
import os
import asyncio
import traceback
import httpx

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.settings import get_settings
from app.modules.extraction.extractor import content_extractor
from app.services.safe_browsing_service import is_ssrf_safe_url
from app.services.news_service import search_duckduckgo, tiered_search
from app.services.tier4 import tier4_verification_service, evidence_ranker, claim_parser, entity_matcher, verdict_engine
from app.core.orchestrator import orchestrator
from app.core.trusted_domains import get_trust_info

settings = get_settings()

async def audit_llm_endpoints():
    print("==================================================")
    print("1. EMPIRICAL LLM ENDPOINT AUDIT (OpenRouter & HF)")
    print("==================================================")
    
    openrouter_key = getattr(settings, "OPENROUTER_API_KEY", None) or os.getenv("OPENROUTER_API_KEY")
    print(f"OPENROUTER_API_KEY Present: {bool(openrouter_key)} (Length: {len(openrouter_key) if openrouter_key else 0})")
    
    if openrouter_key:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openrouter_key}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Cawncade AI",
            "Content-Type": "application/json"
        }
        model = "nvidia/nemotron-3-super-120b-a12b:free"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 10
        }
        
        print(f"\n[OpenRouter Direct HTTP Request]")
        print(f"POST -> {url}")
        print(f"Model Requested: {model}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                print(f"HTTP Status Code: {resp.status_code}")
                print(f"Response Body: {resp.text[:500]}")
        except Exception as e:
            print(f"HTTP Exception: {type(e).__name__}: {e}")
            
    hf_token = getattr(settings, "HUGGINGFACEHUB_API_TOKEN", None) or getattr(settings, "HUGGINGFACE_API_TOKEN", None) or os.getenv("HUGGINGFACEHUB_API_TOKEN")
    print(f"\nHUGGINGFACE_API_TOKEN Present: {bool(hf_token)} (Length: {len(hf_token) if hf_token else 0})")
    
    if hf_token:
        url = "https://router.huggingface.co/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json"
        }
        model = "meta-llama/Llama-3.3-70B-Instruct:groq"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 10
        }
        
        print(f"\n[Hugging Face Router Direct HTTP Request]")
        print(f"POST -> {url}")
        print(f"Model Requested: {model}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                print(f"HTTP Status Code: {resp.status_code}")
                print(f"Response Body: {resp.text[:500]}")
        except Exception as e:
            print(f"HTTP Exception: {type(e).__name__}: {e}")

async def audit_input_classification_and_ssrf():
    print("\n==================================================")
    print("2. INPUT CLASSIFICATION & SSRF AUDIT")
    print("==================================================")
    
    test_inputs = [
        "The Eiffel Tower is located in Paris, France.",
        "https://bbc.com/news",
        "http://169.254.169.254/latest/meta-data/",
        "https://example.com/404",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    ]
    
    for inp in test_inputs:
        is_url_val = content_extractor.is_url(inp)
        is_ssrf_safe, ssrf_reason = is_ssrf_safe_url(inp)
        
        # Test default auto-detection logic
        detected_type = "auto"
        if orchestrator:
            from app.services.youtube_service import is_youtube_url
            if is_youtube_url(inp):
                detected_type = "youtube"
            elif is_url_val:
                detected_type = "url"
            else:
                detected_type = "text"
                
        print(f"\nInput: '{inp}'")
        print(f"  • content_extractor.is_url(): {is_url_val}")
        print(f"  • is_ssrf_safe_url(): safe={is_ssrf_safe}, reason='{ssrf_reason}'")
        print(f"  • Auto-Detected Pipeline Mode: {detected_type}")

async def audit_query_generation_and_retrieval():
    print("\n==================================================")
    print("3. SEARCH QUERY GENERATION & RETRIEVAL AUDIT")
    print("==================================================")
    
    claim = "The James Webb Space Telescope was launched in December 2021."
    print(f"Target Claim: '{claim}'")
    
    # 1. Raw DDG Search
    ddg_res = await search_duckduckgo(claim)
    print(f"\n[DuckDuckGo Raw Retrieval Output ({len(ddg_res)} results)]")
    for idx, r in enumerate(ddg_res[:5], 1):
        print(f"  {idx}. [{r.get('source_name')}] {r.get('title')}")
        print(f"     URL: {r.get('url')}")
        print(f"     Snippet: {r.get('snippet')[:100]}...")

    # 2. Tiered Search
    t_res = await tiered_search(claim)
    sources = t_res.get("sources", [])
    print(f"\n[Tiered Search Output ({len(sources)} results total)]")
    print(f"Tier Stats: {t_res.get('tier_stats')}")
    for idx, s in enumerate(sources[:5], 1):
        print(f"  {idx}. [{s.get('channel')}] {s.get('title')} ({s.get('domain')})")

async def audit_tier4_pipeline_and_trust():
    print("\n==================================================")
    print("4. TIER 4 COMPUTATIONAL ENGINE & TRUST AUDIT")
    print("==================================================")
    
    claim = "Python was created by Guido van Rossum."
    print(f"Claim: '{claim}'")
    
    # Run Orchestrator end-to-end to capture empirical score breakdown
    res = await orchestrator.process(input_text=claim, input_type="auto")
    
    print("\n[Orchestrator Output Summary]")
    print(f"  • Answer / Status: {res.get('answer')}")
    print(f"  • Context Summary: {res.get('context_summary')}")
    print(f"  • Confidence Score: {res.get('confidence')}%")
    print(f"  • Trust Outlets Count: {len(res.get('metadata', {}).get('trusted_domains_found', []))}")
    print(f"  • Sources Retried: {len(res.get('sources_cited', []))}")
    
    print("\n[Source Card Trust Evaluation Check]")
    for idx, s in enumerate(res.get("sources_cited", [])[:5], 1):
        domain = s.get("url", "").split("//")[-1].split("/")[0].replace("www.", "")
        trust_info = get_trust_info(domain)
        print(f"  Source {idx}: {s.get('source_name')} | Domain: {domain}")
        print(f"    - orchestrator is_trusted_domain: {s.get('is_trusted')}")
        print(f"    - get_trust_info(domain): tier={trust_info.get('tier')}, label={trust_info.get('label')}")
        print(f"    - Title: {s.get('title')[:80]}")

async def run_full_audit():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        await audit_llm_endpoints()
        await audit_input_classification_and_ssrf()
        await audit_query_generation_and_retrieval()
        await audit_tier4_pipeline_and_trust()
    except Exception as e:
        print(f"\nCRITICAL AUDIT ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_full_audit())
