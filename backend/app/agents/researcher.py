"""
CAWNCADE AI v3.5 — Researcher Agent.
Uses the tiered search from news_service to find sources.

Fix BUG-01: max_results= → max_sources= to match tiered_search() signature.
"""
from app.services.news_service import tiered_search, verify_against_trusted
from app.utils.logger import log


class ResearcherAgent:
    async def execute(self, query: str, max_sources: int = 10) -> dict:
        log.info(f"[Researcher] Executing tiered search for: '{query[:80]}'")
        return await tiered_search(query, max_sources=max_sources)  # BUG-01 fixed

    async def verify_sources(self, query: str, max_sources: int = 5) -> list:
        log.info(f"[Researcher] Verifying against trusted domains: '{query[:60]}'")
        return await verify_against_trusted(query, max_sources)


researcher = ResearcherAgent()
