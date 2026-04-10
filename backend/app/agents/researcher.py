"""
Researcher Agent.
Role: Perform controlled web search and return structured list of sources.
Tasks: Query search APIs (RSS, GDELT), filter using trusted_sources DB, return structured sources.
"""
from .base import BaseAgent
from ..modules.retrieval.retriever import retriever
from ..modules.ranking.ranker import source_ranker
from ..utils.logger import log


class ResearcherAgent(BaseAgent):
    """
    The Researcher Agent is responsible for finding and collecting
    relevant sources from trusted news outlets and data providers.
    It NEVER lets the LLM browse — all retrieval is backend-controlled.
    """

    def __init__(self):
        super().__init__("ResearcherAgent")

    async def execute(self, query: str, max_sources: int = 8) -> dict:
        """
        Execute research for a given query.
        Returns: {sources: [...], source_count, query}
        """
        if not query or not query.strip():
            return {"sources": [], "source_count": 0, "query": query, "error": "empty_query"}

        log.info(f"[Researcher] Searching for: {query}")

        try:
            # Step 1: Retrieve sources from multiple channels
            raw_sources = await retriever.retrieve_for_query(query, max_sources=max_sources)

            if not raw_sources:
                log.warning(f"[Researcher] No sources found for: {query}")
                return {
                    "sources": [],
                    "source_count": 0,
                    "query": query,
                    "warning": "no_sources_found",
                }

            # Step 2: Rank and select top diverse sources
            ranked_sources = source_ranker.select_top_sources(raw_sources, max_count=max_sources)

            log.info(f"[Researcher] Found {len(ranked_sources)} sources for: {query}")

            return {
                "sources": ranked_sources,
                "source_count": len(ranked_sources),
                "query": query,
            }

        except Exception as e:
            log.error(f"[Researcher] Error: {e}")
            return {
                "sources": [],
                "source_count": 0,
                "query": query,
                "error": str(e),
            }
