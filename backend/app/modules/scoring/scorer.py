import re
from app.utils.logger import log

class ScoringEngine:
    def __init__(self):
        # Fast NLP Token Heuristics
        self.bias_tokens = re.compile(r'\b(obviously|clearly|ridiculous|absurd|destroy|slam|owned|shocking|outrageous|agenda|propaganda|fake|biased)\b', re.IGNORECASE)
        self.sensitivity_tokens = re.compile(r'\b(death|kill|bomb|attack|war|election|fraud|virus|vaccine|illegal|riot|protest|assassination|scandal)\b', re.IGNORECASE)
        self.ai_risk_tokens = re.compile(r'\b(as an ai|language model|delve into|in conclusion|it is important to note|testament to|tapestry|intricate|moreover|furthermore|additionally)\b', re.IGNORECASE)

    def calculate_nlp_heuristic(self, texts, regex_pattern, max_hits=5):
        if not texts:
            return 0.0
        combined_text = " ".join(texts)
        matches = len(regex_pattern.findall(combined_text))
        return min(matches / max_hits, 1.0)

    def compute_score(self, query: str, sources: list) -> dict:
        if not sources:
            return {
                "confidence": 0.0,
                "bias": 0.0,
                "conflict": 0.0,
                "sensitivity": 0.0,
                "ai_risk": 0.0,
                "recency": 0.0,
                "confidence_label": "INSUFFICIENT"
            }
            
        texts = [s.get("title", "") + " " + s.get("snippet", "") for s in sources]
        all_texts = [query] + texts
        
        # 1. Recency
        recency_avg = sum(s.get("recency_score", 0.5) for s in sources) / len(sources)
        
        # 2. Conflict (Structural heuristic based on domain diversity vs trust)
        domains = set(s.get("domain", "") for s in sources)
        trusted_ratio = len([s for s in sources if s.get("is_trusted_domain")]) / len(sources)
        conflict_score = max(0.0, min((len(domains) / 10) - (trusted_ratio * 0.5), 1.0))
        
        # 3. Bias
        bias_score = self.calculate_nlp_heuristic(texts, self.bias_tokens, max_hits=8)
        
        # 4. Sensitivity
        sensitivity_score = self.calculate_nlp_heuristic(all_texts, self.sensitivity_tokens, max_hits=3)
        
        # 5. AI Risk
        ai_risk_score = self.calculate_nlp_heuristic(texts, self.ai_risk_tokens, max_hits=5)
        
        # 6. Confidence
        credibility_avg = sum(s.get("credibility_score", 0.5) for s in sources) / len(sources)
        base_confidence = (credibility_avg * 0.6) + (trusted_ratio * 0.4)
        penalty = (bias_score * 0.1) + (conflict_score * 0.15) + (ai_risk_score * 0.1)
        confidence = max(0.0, min(base_confidence - penalty, 1.0))
        
        return {
            "confidence": round(confidence, 4),
            "bias": round(bias_score, 4),
            "conflict": round(conflict_score, 4),
            "sensitivity": round(sensitivity_score, 4),
            "ai_risk": round(ai_risk_score, 4),
            "recency": round(recency_avg, 4),
            "confidence_label": self._get_confidence_label(confidence)
        }

    def _get_confidence_label(self, confidence):
        if confidence >= 0.8:
            return "HIGH"
        elif confidence >= 0.6:
            return "MODERATE"
        elif confidence >= 0.4:
            return "LOW"
        else:
            return "INSUFFICIENT"

scoring_engine = ScoringEngine()
