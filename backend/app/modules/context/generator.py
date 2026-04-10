"""
Context Generator Module.
Builds structured context from verified sources for LLM synthesis.
This is the RAG context builder — feeds clean, verified data to the LLM.
"""
from ...utils.logger import log
from ...utils.helpers import format_sources_for_prompt, truncate_text


class ContextGenerator:
    """
    Generates structured context for the Synthesizer Agent.
    Combines verified source data into a clean prompt context.
    """

    def __init__(self):
        self.max_context_length = 6000  # characters, to stay within model limits

    def build_context(
        self,
        query: str,
        sources: list[dict],
        verification: dict,
        tfidf_result: dict = None,
    ) -> dict:
        """
        Build complete context package for LLM synthesis.
        Returns dict with: formatted_context, source_count, metadata
        """
        source_count = len(sources)
        if source_count == 0:
            return {
                "formatted_context": f"Query: {query}\n\nNo sources could be retrieved. Unable to verify.",
                "source_count": 0,
                "metadata": {"has_sources": False, "has_verification": False},
            }

        # Build source section
        source_text = format_sources_for_prompt(sources)

        # Build verification section
        verification_text = self._format_verification(verification)

        # Build TF-IDF section
        tfidf_text = ""
        if tfidf_result:
            tfidf_text = f"\n[Baseline Signal]\nTF-IDF suspicion score: {tfidf_result.get('tfidf_suspicion_score', 'N/A')}\n"
            if tfidf_result.get("keywords"):
                tfidf_text += f"Key terms: {', '.join(tfidf_result['keywords'][:8])}\n"

        # Combine into final context
        context_parts = [
            f"[Query Under Analysis]\n{query}\n",
            f"[Retrieved Sources ({source_count})]\n{source_text}\n",
            verification_text,
            tfidf_text,
        ]

        full_context = "\n".join(context_parts)

        # Truncate if too long
        if len(full_context) > self.max_context_length:
            full_context = truncate_text(full_context, self.max_context_length)

        metadata = {
            "has_sources": source_count > 0,
            "source_count": source_count,
            "has_verification": bool(verification.get("agreements") or verification.get("conflicts")),
            "agreement_count": len(verification.get("agreements", [])),
            "conflict_count": len(verification.get("conflicts", [])),
            "avg_credibility": sum(s.get("credibility_score", 0) for s in sources) / source_count if sources else 0,
        }

        return {
            "formatted_context": full_context,
            "source_count": source_count,
            "metadata": metadata,
        }

    def _format_verification(self, verification: dict) -> str:
        """Format verification results into readable text."""
        if not verification:
            return ""

        lines = ["[Source Verification]\n"]

        agreements = verification.get("agreements", [])
        if agreements:
            lines.append("Agreements found:")
            for a in agreements[:5]:  # Limit to 5
                lines.append(f"  - {a.get('source_1')} ↔ {a.get('source_2')} (similarity: {a.get('similarity', 'N/A'):.2f})")
            lines.append("")

        conflicts = verification.get("conflicts", [])
        if conflicts:
            lines.append("Potential conflicts detected:")
            for c in conflicts[:5]:
                lines.append(f"  - {c.get('source_1')} ↔ {c.get('source_2')} (similarity: {c.get('similarity', 'N/A'):.2f})")
            lines.append("")

        scores = {
            "agreement_score": verification.get("agreement_score"),
            "conflict_score": verification.get("conflict_score"),
            "diversity_score": verification.get("diversity_score"),
            "coverage_score": verification.get("coverage_score"),
        }
        score_lines = [f"  {k}: {v:.2f}" for k, v in scores.items() if v is not None]
        if score_lines:
            lines.append("Verification scores:")
            lines.extend(score_lines)
            lines.append("")

        return "\n".join(lines)


# Singleton
context_generator = ContextGenerator()
