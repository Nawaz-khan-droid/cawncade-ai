"""
Scoring Engine v3.0.
Computes the final confidence score using the CAWNCADE formula.
"""
from app.config.settings import get_settings
from app.utils.logger import log
from app.utils.helpers import normalize_score

settings = get_settings()


class ScoringEngine:
    def __init__(self):
        self.weights = {
            "credibility": settings.W_CREDIBILITY,
            "agreement": settings.W_AGREEMENT,
            "diversity": settings.W_DIVERSITY,
            "recency": settings.W_RECENCY,
            "grounding": settings.W_GROUNDING,
        }
        self.bias_threshold = settings.PENALTY_BIAS_THRESHOLD
        self.conflict_threshold = settings.PENALTY_CONFLICT_THRESHOLD
        self.ai_risk_threshold = settings.PENALTY_AI_RISK_THRESHOLD

    def compute_score(self, credibility_avg, agreement_score, diversity_score,
                       recency_score, grounding_score, tfidf_suspicion=0.0,
                       bias_score=0.0, conflict_score=0.0, ai_risk_score=0.0) -> dict:
        credibility_avg = normalize_score(credibility_avg)
        agreement_score = normalize_score(agreement_score)
        diversity_score = normalize_score(diversity_score)
        recency_score = normalize_score(recency_score)
        grounding_score = normalize_score(grounding_score)
        tfidf_suspicion = normalize_score(tfidf_suspicion)
        bias_score = normalize_score(bias_score)
        conflict_score = normalize_score(conflict_score)
        ai_risk_score = normalize_score(ai_risk_score)

        base_confidence = (
            self.weights["credibility"] * credibility_avg
            + self.weights["agreement"] * agreement_score
            + self.weights["diversity"] * diversity_score
            + self.weights["recency"] * recency_score
            + self.weights["grounding"] * grounding_score
        )

        bias_penalty = 0.0
        if bias_score > self.bias_threshold:
            bias_penalty = (bias_score - self.bias_threshold) * 0.5

        conflict_penalty = 0.0
        if conflict_score > self.conflict_threshold:
            conflict_penalty = (conflict_score - self.conflict_threshold) * 0.4

        ai_risk_penalty = 0.0
        if ai_risk_score > self.ai_risk_threshold:
            ai_risk_penalty = (ai_risk_score - self.ai_risk_threshold) * 0.3

        suspicion_penalty = tfidf_suspicion * 0.15
        total_penalty = bias_penalty + conflict_penalty + ai_risk_penalty + suspicion_penalty
        confidence = normalize_score(base_confidence - total_penalty)

        disclaimers = self._generate_disclaimers(credibility_avg, diversity_score, agreement_score, conflict_score, bias_score, ai_risk_score, confidence)

        return {
            "confidence_score": round(confidence, 4),
            "credibility_avg": round(credibility_avg, 4),
            "agreement_score": round(agreement_score, 4),
            "diversity_score": round(diversity_score, 4),
            "recency_score": round(recency_score, 4),
            "grounding_score": round(grounding_score, 4),
            "bias_score": round(bias_score, 4),
            "conflict_score": round(conflict_score, 4),
            "ai_risk_score": round(ai_risk_score, 4),
            "tfidf_suspicion_score": round(tfidf_suspicion, 4),
            "bias_penalty": round(bias_penalty, 4),
            "conflict_penalty": round(conflict_penalty, 4),
            "ai_risk_penalty": round(ai_risk_penalty, 4),
            "suspicion_penalty": round(suspicion_penalty, 4),
            "dynamic_disclaimers": disclaimers,
            "confidence_label": self._get_confidence_label(confidence),
        }

    def _generate_disclaimers(self, credibility, diversity, agreement, conflict, bias, ai_risk, confidence):
        disclaimers = []
        if credibility < 0.5:
            disclaimers.append("Sources with low average credibility. Verify with additional sources.")
        if diversity < 0.3:
            disclaimers.append("Low source diversity. Most sources may come from similar perspectives.")
        if conflict > 0.5:
            disclaimers.append("Significant conflicting information detected. Multiple narratives exist.")
        if bias > 0.3:
            disclaimers.append("Potential bias detected in source selection or framing.")
        if ai_risk > 0.5:
            disclaimers.append("Content may be AI-generated or manipulated. Exercise caution.")
        if confidence < 0.3:
            disclaimers.append("Insufficient evidence for confident assessment. Seek more sources.")
        if agreement > 0.8:
            disclaimers.append("Strong agreement across sources on this topic.")
        return disclaimers

    def _get_confidence_label(self, confidence):
        if confidence >= 0.8:
            return "HIGH - Strong evidence support"
        elif confidence >= 0.6:
            return "MODERATE - Generally supported by sources"
        elif confidence >= 0.4:
            return "LOW - Mixed or limited evidence"
        elif confidence >= 0.2:
            return "VERY LOW - Significant uncertainty"
        else:
            return "INSUFFICIENT - Cannot reliably assess"


scoring_engine = ScoringEngine()
