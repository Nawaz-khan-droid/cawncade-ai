import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app.services.news_service import search_duckduckgo, search_google_news_rss, search_gdelt, tiered_search

async def test():
    print("Testing DDG...")
    ddg = await search_duckduckgo("NASA Europa Clipper 2024")
    print(f"DDG count: {len(ddg)}")
    
    print("Testing RSS...")
    rss = await search_google_news_rss("NASA Europa Clipper 2024")
    print(f"RSS count: {len(rss)}")
    
    print("Testing GDELT...")
    gdelt = await search_gdelt("NASA Europa Clipper 2024")
    print(f"GDELT count: {len(gdelt)}")
    
    print("Testing Tiered Search...")
    ts = await tiered_search(["NASA Europa Clipper 2024"])
    print(f"Tiered Search count: {len(ts.get('sources', []))}")
    if ts.get('sources'):
        for s in ts['sources'][:3]:
            print(" -", s.get('source_name'), "|", s.get('title'))

if __name__ == "__main__":
    asyncio.run(test())
