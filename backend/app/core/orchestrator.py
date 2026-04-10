"""
Pipeline Orchestrator.
Coordinates the full analysis pipeline: Extract → Retrieve → Verify → Score → Synthesize.
This is the brain of CAWNCADE AI.
"""
import time
from typing import Optional
from ..agents.researcher import ResearcherAgent
from ..agents.verifier import VerifierAgent
from ..agents.synthesizer import SynthesizerAgent
from ..modules.scoring.scorer import scoring_engine
from ..modules.extraction.extractor import content_extractor
from ..utils.logger import log
from ..utils.helpers import compute_recency


class Orchestrator:
    """
    Main pipeline orchestrator for CAWNCADE AI.
    Coordinates all agents in sequence, passing data between stages.
    """

    def __init__(self):
        self.researcher = ResearcherAgent()
        self.verifier = VerifierAgent()
        self.synthesizer = SynthesizerAgent()

    async def process(
        self,
        input_text: str,
        input_type: str = "text",
        max_sources: int = 8,
    ) -> dict:
        """
        Full analysis pipeline.
        Steps:
          1. Extract (if URL) or use raw text
          2. Research (retrieve sources)
          3. Verify (analyze sources)
          4. Score (compute confidence)
          5. Synthesize (generate output)

        Returns: Complete analysis result dict.
        """
        start_time = time.time()

        # Step 1: Input handling
        query = input_text
        if input_type == "url" and input_text.startswith(("http://", "https://")):
            extraction_result = await content_extractor.extract_from_url(input_text)
            if extraction_result.get("text"):
                query = f"{extraction_result.get('title', '')} {extraction_result.get('text', '')[:500]}"
                log.info(f"[Orchestrator] Extracted from URL: {extraction_result.get('title', 'N/A')}")
            else:
                log.warning(f"[Orchestrator] URL extraction failed, using raw input.")
                query = input_text

        # Step 2: Research — retrieve sources
        research_result = await self.researcher.execute(query=query, max_sources=max_sources)
        sources = research_result.get("sources", [])

        if not sources:
            compute_time = int((time.time() - start_time) * 1000)
            return {
                "answer": "No relevant sources could be retrieved for this query. Try rephrasing or providing more specific details.",
                "context_summary": "Retrieval returned no results.",
                "agreements": [],
                "conflicts": [],
                "sources_cited": [],
                "confidence": 0.0,
                "scores": {
                    "confidence_score": 0.0,
                    "confidence_label": "INSUFFICIENT — Cannot reliably assess",
                    "dynamic_disclaimers": ["No sources found for verification."],
                },
                "compute_time_ms": compute_time,
                "status": "no_sources",
            }

        # Step 3: Verify — cross-source analysis + TF-IDF
        verify_result = await self.verifier.execute(
            sources=sources,
            query=query,
            input_text=input_text,
        )
        verification = verify_result.get("verification", {})
        tfidf_result = verify_result.get("tfidf_result", {})

        # Step 4: Score — compute confidence
        credibility_avg = sum(s.get("credibility_score", 0.5) for s in sources) / len(sources)
        recency_avg = sum(
            compute_recency(s.get("published_at"))
            for s in sources
        ) / len(sources)

        scores = scoring_engine.compute_score(
            credibility_avg=credibility_avg,
            agreement_score=verification.get("agreement_score", 0.5),
            diversity_score=verification.get("diversity_score", 0.3),
            recency_score=recency_avg,
            grounding_score=verification.get("coverage_score", 0.3),
            tfidf_suspicion=tfidf_result.get("tfidf_suspicion_score", 0.0),
            bias_score=0.0,  # Future: integrate bias detection model
            conflict_score=verification.get("conflict_score", 0.0),
            ai_risk_score=0.0,  # Future: integrate AI content detection
        )

        # Step 5: Synthesize — generate final output
        synthesis_result = await self.synthesizer.execute(
            query=query,
            sources=sources,
            verification=verification,
            scores=scores,
            tfidf_result=tfidf_result,
        )

        compute_time = int((time.time() - start_time) * 1000)

        # Combine all results
        final_result = {
            "answer": synthesis_result.get("answer", ""),
            "context_summary": synthesis_result.get("context_summary", ""),
            "agreements": synthesis_result.get("agreements", []),
            "conflicts": synthesis_result.get("conflicts", []),
            "sources_cited": synthesis_result.get("sources_cited", []),
            "confidence": scores.get("confidence_score", 0.0),
            "scores": scores,
            "compute_time_ms": compute_time,
            "status": "completed",
            "metadata": {
                "sources_retrieved": len(sources),
                "agreements_found": len(verification.get("agreements", [])),
                "conflicts_found": len(verification.get("conflicts", [])),
                "tfidf_suspicion": tfidf_result.get("tfidf_suspicion_score", 0),
            },
        }

        log.info(
            f"[Orchestrator] Pipeline completed in {compute_time}ms. "
            f"Confidence: {scores.get('confidence_score', 0):.2f} "
            f"({scores.get('confidence_label', 'N/A')})"
        )

        return final_result


# Singleton
orchestrator = Orchestrator()
