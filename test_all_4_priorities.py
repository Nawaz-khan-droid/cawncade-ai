import asyncio
import sys

sys.path.insert(0, 'backend')
from app.services.news_service import search_gdelt, tiered_search
from app.services.agent_service import CawncadeAgent
from app.core.cache import cache

async def test_priorities():
    print("=================== TESTING ALL 4 PRIORITIES AUDIT ===================")
    
    # Priority 4: GDELT Live Execution Check
    print("\n1. GDELT v2 API Execution Check:")
    gdelt_articles = await search_gdelt("NASA Europa Clipper", max_results=3)
    print(f"   Retrieved {len(gdelt_articles)} articles directly from GDELT API:")
    for a in gdelt_articles:
        print(f"     - [{a['source_name']}] {a['title'][:60]} ({a['url']})")

    # Priority 3: Provider Health Memory Caching Check
    print("\n2. Provider Health Memory Caching Check:")
    cache.set("provider_health:openrouter", "RATE_LIMITED", ttl=3600)
    print("   Cached 'provider_health:openrouter' -> RATE_LIMITED")
    agent = CawncadeAgent()
    try:
        agent._init_agent()
    except Exception as e:
        print(f"   Agent initialization output: {e}")
    print(f"   Active Model Tier: {agent.llm_tier}")

    # Priority 2: Stance & Relevance-Aware Early Stopping
    print("\n3. Stance & Relevance-Aware Early Stopping Check:")
    search_res = await tiered_search(["NASA Europa Clipper launch 2024", "NASA Europa Clipper fact check"])
    print(f"   Queries Executed : {search_res.get('queries_executed')}")
    print(f"   Early Stopped    : {search_res.get('early_stopped')}")
    print(f"   Sources Found    : {len(search_res.get('sources', []))}")

if __name__ == "__main__":
    asyncio.run(test_priorities())
