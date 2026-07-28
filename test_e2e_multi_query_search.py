import asyncio
import sys
import json

sys.path.insert(0, 'backend')
from app.services.tier4.claim_parser import claim_parser
from app.services.news_service import tiered_search

async def test_multi_query_retrieval():
    raw_claim = "WHO says vaccine X reduced deaths by 40% in 2024 in India"
    print("=================== E2E MULTI-QUERY SEARCH VERIFICATION ===================")
    print("Raw Claim Input:", raw_claim)

    expanded = claim_parser.generate_expanded_queries(raw_claim)
    print("\nGenerated Expanded Query Set:")
    for i, q in enumerate(expanded, 1):
        print(f"  Query {i}: {q}")

    print("\nExecuting Parallel Search across expanded queries...")
    res = await tiered_search(expanded, max_sources=10)

    print("\nSearch Execution Summary:")
    print("Queries Executed:", res.get("queries_executed"))
    print("Total Found Articles:", res.get("total_found"))
    print("Deduplicated Unique Domain Sources:", len(res.get("sources", [])))
    
    for i, src in enumerate(res.get("sources", [])[:5], 1):
        print(f"  Source {i}: [{src.get('domain')}] {src.get('title')[:60]} ({src.get('url')})")

if __name__ == "__main__":
    asyncio.run(test_multi_query_retrieval())
