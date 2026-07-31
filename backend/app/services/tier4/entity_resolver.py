"""
CAWNCADE AI v3.5 — Entity Resolution & Linking Engine.
Resolves ambiguous or generic entity mentions to canonical entity definitions.
"""
import re
from typing import Dict, Any

ENTITY_KNOWLEDGE_BASE = {
    # Vaccines & Medical Products
    r"\b(vaccine\s+x|covid\s+vaccine|corona\s+shot|mrna\s+vaccine)\b": [
        {"entity": "COVID-19 Vaccine (mRNA)", "confidence": 0.42, "category": "Medical Product"},
        {"entity": "Experimental Candidate Vaccine", "confidence": 0.35, "category": "Medical Candidate"},
    ],
    r"\b(polio\s+vaccine|ipv|opv)\b": [
        {"entity": "Polio Vaccine (Salk / Sabin)", "confidence": 0.85, "category": "Medical Product"},
    ],
    # Space & Science Missions
    r"\b(europa\s+clipper|europa\s+probe|europa\s+spacecraft)\b": [
        {"entity": "NASA Europa Clipper Spacecraft", "confidence": 0.90, "category": "Space Mission"},
    ],
    r"\b(james\s+webb|jwst|webb\s+telescope)\b": [
        {"entity": "James Webb Space Telescope (JWST)", "confidence": 0.92, "category": "Space Telescope"},
    ],
    # Health Organizations
    r"\b(who|world\s+health\s+org|world\s+health\s+organization)\b": [
        {"entity": "World Health Organization (WHO)", "confidence": 0.95, "category": "Health Agency"},
    ]
}


class EntityResolver:
    """Probabilistic entity linking returning candidate matches with explicit confidence scores."""

    def resolve_entities(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        candidates = []

        for pattern, cand_list in ENTITY_KNOWLEDGE_BASE.items():
            if re.search(pattern, text_lower):
                candidates.extend(cand_list)

        # High confidence threshold for search query inclusion (confidence >= 0.70)
        high_conf_entities = [c["entity"] for c in candidates if c["confidence"] >= 0.70]

        return {
            "input": text,
            "candidates": candidates,
            "high_confidence_entities": high_conf_entities,
            # EDGE-05 FIX: entity_aliases was missing — claim_parser.generate_expanded_queries
            # calls linked.get('entity_aliases') to build enriched search queries.
            # Without this key, that branch was permanently dead code.
            "entity_aliases": [c["entity"] for c in candidates],
        }


entity_resolver = EntityResolver()
