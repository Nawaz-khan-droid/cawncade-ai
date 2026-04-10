"""
Synthesizer Agent.
Role: Generate final context-aware explanation using retrieved data.
Rules: Use ONLY retrieved data, cite all sources, highlight uncertainty, compare narratives.
"""
from .base import BaseAgent
from ..modules.context.generator import context_generator
from ..services.llm_service import llm_service
from ..utils.logger import log


class SynthesizerAgent(BaseAgent):
    """
    The Synthesizer Agent generates the final human-readable output.
    It uses ONLY data passed from the Verifier and Context Generator.
    It NEVER fabricates sources or claims.
    """

    def __init__(self):
        super().__init__("SynthesizerAgent")
        self.system_prompt = (
            "You are CAWNCADE AI, a context-aware news verification assistant. "
            "Your role is to synthesize information from MULTIPLE retrieved sources into a balanced, factual summary.\n\n"
            "CRITICAL RULES:\n"
            "1. Use ONLY the information provided in the context. Never hallucinate or fabricate.\n"
            "2. Cite every claim with [Source N] reference.\n"
            "3. If sources conflict, acknowledge BOTH sides and explain the disagreement.\n"
            "4. If evidence is insufficient, explicitly say 'Insufficient evidence to confirm or deny.'\n"
            "5. Never claim absolute truth. Use phrases like 'according to sources', 'evidence suggests', 'reports indicate'.\n"
            "6. Compare different narratives if they exist. Note what each source emphasizes.\n"
            "7. Highlight gaps in coverage or missing information.\n"
            "8. Keep your response factual, balanced, and neutral. Avoid editorializing.\n"
            "9. Structure your response with clear sections: Summary, Key Findings, Source Comparison, Gaps & Uncertainty.\n"
            "10. If the content appears to be AI-generated or manipulated, flag this clearly."
        )

    async def execute(
        self,
        query: str,
        sources: list[dict],
        verification: dict,
        scores: dict,
        tfidf_result: dict = None,
    ) -> dict:
        """
        Synthesize final output from all available data.
        Returns: {answer, context_summary, agreements, conflicts, sources_cited, confidence}
        """
        if not sources:
            return {
                "answer": "Insufficient evidence to assess this claim. No reliable sources could be retrieved for verification.",
                "context_summary": "No sources available.",
                "agreements": [],
                "conflicts": [],
                "sources_cited": [],
                "confidence": 0.0,
            }

        log.info(f"[Synthesizer] Generating synthesis for {len(sources)} sources.")

        try:
            # Step 1: Build context from verified sources
            context_data = context_generator.build_context(
                query=query,
                sources=sources,
                verification=verification,
                tfidf_result=tfidf_result,
            )

            # Step 2: Build synthesis prompt
            prompt = self._build_synthesis_prompt(
                query=query,
                context=context_data["formatted_context"],
                scores=scores,
                confidence_label=scores.get("confidence_label", "UNKNOWN"),
            )

            # Step 3: Generate synthesis via LLM
            answer = await llm_service.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                max_tokens=1200,
                temperature=0.3,
            )

            # Step 4: Fallback if LLM fails
            if not answer or len(answer) < 50:
                answer = self._generate_fallback_synthesis(query, sources, verification, scores)

            # Step 5: Format source citations
            sources_cited = [
                {
                    "name": s.get("source_name", "Unknown"),
                    "url": s.get("url", ""),
                    "credibility": round(s.get("credibility_score", 0), 2),
                }
                for s in sources
            ]

            return {
                "answer": answer,
                "context_summary": f"Based on {len(sources)} sources. {context_data['metadata'].get('agreement_count', 0)} agreements, {context_data['metadata'].get('conflict_count', 0)} potential conflicts detected.",
                "agreements": [
                    {
                        "source_1": a.get("source_1"),
                        "source_2": a.get("source_2"),
                        "similarity": round(a.get("similarity", 0), 2),
                    }
                    for a in verification.get("agreements", [])[:5]
                ],
                "conflicts": [
                    {
                        "source_1": c.get("source_1"),
                        "source_2": c.get("source_2"),
                        "similarity": round(c.get("similarity", 0), 2),
                    }
                    for c in verification.get("conflicts", [])[:5]
                ],
                "sources_cited": sources_cited,
                "confidence": scores.get("confidence_score", 0.0),
            }

        except Exception as e:
            log.error(f"[Synthesizer] Error: {e}")
            return {
                "answer": "An error occurred during synthesis. Please review the source scores and verification results manually.",
                "context_summary": "Synthesis failed due to an error.",
                "agreements": [],
                "conflicts": [],
                "sources_cited": [],
                "confidence": 0.0,
                "error": str(e),
            }

    def _build_synthesis_prompt(self, query: str, context: str, scores: dict, confidence_label: str) -> str:
        """Build the full prompt for LLM synthesis."""
        return f"""Analyze the following claim using the provided sources:

CLAIM/QUERY: {query}

{context}

VERIFICATION METRICS:
- Confidence Level: {confidence_label}
- Source Agreement: {scores.get('agreement_score', 'N/A')}
- Source Diversity: {scores.get('diversity_score', 'N/A')}
- Average Source Credibility: {scores.get('credibility_avg', 'N/A')}

DYNAMIC DISCLAIMERS: {', '.join(scores.get('dynamic_disclaimers', [])) if scores.get('dynamic_disclaimers') else 'None'}

Based ONLY on the sources above, provide:
1. SUMMARY: Brief factual summary of what the sources collectively say
2. KEY FINDINGS: Main points supported by evidence
3. SOURCE COMPARISON: How different sources frame this topic
4. GAPS & UNCERTAINTY: What's missing or unclear

Remember: If evidence is insufficient, say so explicitly. Do not fabricate information."""

    def _generate_fallback_synthesis(self, query: str, sources: list[dict], verification: dict, scores: dict) -> str:
        """Generate a basic synthesis without LLM (when API is unavailable)."""
        confidence = scores.get("confidence_score", 0.0)
        label = scores.get("confidence_label", "UNKNOWN")

        parts = [
            f"## Context-Aware Analysis: {query}",
            f"\n**Confidence Level:** {label} ({confidence:.1%})",
            f"\n**Sources Analyzed:** {len(sources)}",
        ]

        # Add credibility info
        high_cred = [s for s in sources if s.get("credibility_score", 0) >= 0.8]
        if high_cred:
            parts.append(f"\n**High-credibility sources:** {', '.join(s.get('source_name', '?') for s in high_cred[:3])}")

        # Add agreements
        agreements = verification.get("agreements", [])
        if agreements:
            parts.append(f"\n**Source Agreement:** {len(agreements)} agreement(s) detected between sources.")

        # Add conflicts
        conflicts = verification.get("conflicts", [])
        if conflicts:
            parts.append(f"\n**Source Conflicts:** {len(conflicts)} potential conflict(s) detected. Different sources may present different narratives.")

        # Add disclaimers
        disclaimers = scores.get("dynamic_disclaimers", [])
        if disclaimers:
            parts.append("\n**Warnings:**")
            for d in disclaimers:
                parts.append(f"- {d}")

        parts.append("\n*Note: AI synthesis unavailable. Review sources manually for full analysis.*")

        return "\n".join(parts)
