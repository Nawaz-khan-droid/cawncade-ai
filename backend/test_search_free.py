import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app.services.news_service import search_duckduckgo, search_google_news_rss, tiered_search

async def test():
    query = "Elon Musk Twitter purchase"
    print("Testing DDG for:", query)
    ddg = await search_duckduckgo(query)
    print(f"DDG count: {len(ddg)}")
    for s in ddg[:3]:
        print("  -", s.get("source_name"), "|", s.get("title"))
    
    print("\nTesting RSS for:", query)
    rss = await search_google_news_rss(query)
    print(f"RSS count: {len(rss)}")
    for s in rss[:3]:
        print("  -", s.get("source_name"), "|", s.get("title"))

    print("\nTesting Tiered Search...")
    ts = await tiered_search(["Did Elon musk buy Twitter ?"])
    print(f"Tiered Search count: {len(ts.get('sources', []))}")
    for s in ts.get('sources', [])[:5]:
        print("  -", s.get("source_name"), "|", s.get("title"))

if __name__ == "__main__":
    asyncio.run(test())
