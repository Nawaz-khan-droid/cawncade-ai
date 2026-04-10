"""
Verifier Agent.
Role: Analyze retrieved sources for agreement, conflict, and credibility.
Tasks: Detect agreement, detect conflicts, integrate fact-check data, assign credibility weights.
"""
from .base import BaseAgent
from ..modules.verification.verifier import source_verifier
from ..modules.text.tfidf_module import tfidf_model
from ..utils.logger import log


class VerifierAgent(BaseAgent):
    """
    The Verifier Agent analyzes all retrieved sources together
    to detect patterns of agreement, conflict, bias, and coverage gaps.
    """

    def __init__(self):
        super().__init__("VerifierAgent")

    async def execute(self, sources: list[dict], query: str, input_text: str = "") -> dict:
        """
        Verify sources against the query and input text.
        Returns: verification results with agreement, conflict, TF-IDF signal.
        """
        if not sources:
            log.warning("[Verifier] No sources to verify.")
            return {
                "verification": {
                    "agreements": [],
                    "conflicts": [],
                    "agreement_score": 0.0,
                    "conflict_score": 0.0,
                    "diversity_score": 0.0,
                    "coverage_score": 0.0,
                },
                "tfidf_result": {"tfidf_suspicion_score": 0.3, "keywords": [], "model_trained": False},
            }

        log.info(f"[Verifier] Analyzing {len(sources)} sources.")

        try:
            # Step 1: Cross-source verification
            verification = source_verifier.verify_sources(sources, query)

            # Step 2: TF-IDF baseline signal on input text
            tfidf_result = {}
            if input_text:
                tfidf_result = tfidf_model.predict(input_text)
            else:
                # Use query as fallback
                tfidf_result = tfidf_model.predict(query)

            log.info(
                f"[Verifier] Agreement: {verification['agreement_score']:.2f}, "
                f"Conflict: {verification['conflict_score']:.2f}, "
                f"TF-IDF suspicion: {tfidf_result.get('tfidf_suspicion_score', 'N/A')}"
            )

            return {
                "verification": verification,
                "tfidf_result": tfidf_result,
            }

        except Exception as e:
            log.error(f"[Verifier] Error: {e}")
            return {
                "verification": {
                    "agreements": [],
                    "conflicts": [],
                    "agreement_score": 0.5,
                    "conflict_score": 0.0,
                    "diversity_score": 0.3,
                    "coverage_score": 0.3,
                    "error": str(e),
                },
                "tfidf_result": {"tfidf_suspicion_score": 0.3, "keywords": [], "model_trained": False},
            }
