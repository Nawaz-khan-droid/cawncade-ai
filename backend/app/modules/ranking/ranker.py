"""
Ranking Module.
Ranks retrieved sources by relevance, credibility, and recency.
"""
from ...utils.logger import log
from ...utils.helpers import normalize_score


class SourceRanker:
    """Rank sources using weighted combination of multiple signals."""

    def __init__(self, weights: dict = None):
        self.weights = weights or {
            "relevance": 0.35,
            "credibility": 0.30,
            "recency": 0.20,
            "diversity": 0.15,
        }

    def rank_sources(self, sources: list[dict]) -> list[dict]:
        """
        Rank and sort sources. Also computes diversity bonus.
        Modifies sources in-place and returns them sorted.
        """
        if not sources:
            return []

        # Compute diversity: how many unique source domains/regions
        domains = set(s.get("domain") for s in sources)
        regions = set(s.get("source_region", "unknown") for s in sources)
        diversity_ratio = min(len(domains) / max(len(sources), 1), 1.0)
        region_diversity = min(len(regions) / 3.0, 1.0)  # 3+ regions = max diversity

        for src in sources:
            relevance = src.get("relevance_score", 0.5)
            credibility = src.get("credibility_score", 0.5)
            recency = src.get("recency_score", 0.5)

            # Diversity bonus: boost underrepresented domains
            domain_count = sum(1 for s in sources if s.get("domain") == src.get("domain"))
            diversity_bonus = 1.0 / domain_count  # Penalize clusters from same source

            final_score = normalize_score(
                self.weights["relevance"] * relevance
                + self.weights["credibility"] * credibility
                + self.weights["recency"] * recency
                + self.weights["diversity"] * diversity_bonus * region_diversity
            )

            src["final_rank_score"] = final_score

        # Sort by final rank score descending
        sources.sort(key=lambda x: x.get("final_rank_score", 0), reverse=True)
        return sources

    def select_top_sources(self, sources: list[dict], max_count: int = 8) -> list[dict]:
        """Select top N diverse sources."""
        ranked = self.rank_sources(sources)
        selected = []
        seen_domains = set()

        for src in ranked:
            domain = src.get("domain")
            # Ensure domain diversity in selection
            if domain not in seen_domains or len(selected) < max_count // 2:
                selected.append(src)
                seen_domains.add(domain)
            if len(selected) >= max_count:
                break

        return selected


# Singleton
source_ranker = SourceRanker()
