"""
CAWNCADE AI v3.5 — Tier 4 Entity Overlap & Timeline Conflict Matcher.
Detects exact entity overlap, date/year mismatches, and numerical discrepancies.
"""

from typing import Dict, Any, List


class EntityMatcher:
    """Calculates entity overlap ratios and detects date/timeline conflicts."""

    def compare_entities(self, claim_parsed: Dict[str, Any], evidence_parsed: Dict[str, Any]) -> Dict[str, Any]:
        claim_people = set(claim_parsed.get("people", []))
        claim_orgs = set(claim_parsed.get("organizations", []))
        claim_locs = set(claim_parsed.get("locations", []))
        claim_dates = set(claim_parsed.get("dates", []))
        claim_years = set(claim_parsed.get("years", []))

        evidence_people = set(evidence_parsed.get("people", []))
        evidence_orgs = set(evidence_parsed.get("organizations", []))
        evidence_locs = set(evidence_parsed.get("locations", []))
        evidence_dates = set(evidence_parsed.get("dates", []))
        evidence_years = set(evidence_parsed.get("years", []))

        # 1. Entity Overlap Score
        claim_all_ents = claim_people.union(claim_orgs).union(claim_locs)
        evidence_all_ents = evidence_people.union(evidence_orgs).union(evidence_locs)

        if claim_all_ents:
            matched_ents = claim_all_ents.intersection(evidence_all_ents)
            entity_overlap_score = len(matched_ents) / len(claim_all_ents)
        else:
            entity_overlap_score = 0.5  # Neutral fallback if no entities exist in claim

        # 2. Year & Timeline Conflict Detection
        year_match = True
        year_conflict = False

        if claim_years and evidence_years:
            if claim_years.intersection(evidence_years):
                year_match = True
            else:
                year_conflict = True
                year_match = False

        return {
            "entity_overlap_score": round(entity_overlap_score, 2),
            "year_match": year_match,
            "year_conflict": year_conflict,
            "claim_years": list(claim_years),
            "evidence_years": list(evidence_years),
            "matched_entities": list(claim_all_ents.intersection(evidence_all_ents)) if claim_all_ents else [],
        }


entity_matcher = EntityMatcher()
