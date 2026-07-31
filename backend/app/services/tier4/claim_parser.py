"""
CAWNCADE AI v3.5 — Tier 4 Claim Decomposition Parser.
Decomposes user claims into structured subjects, actions, dates, numbers, and entities.
"""

import re  # REFACTOR-06 FIX: import at module level, not inside functions
from typing import Dict, Any, List
from app.utils.logger import log

try:
    import spacy
    try:
        nlp_spacy = spacy.load("en_core_web_sm")
    except Exception:
        nlp_spacy = spacy.blank("en")
    HAS_SPACY = True
except Exception:
    HAS_SPACY = False


class ClaimParser:
    """Decomposes text claims into structured linguistic components & scored search queries."""

    def parse_claim(self, claim_text: str) -> Dict[str, Any]:
        result = {
            "text": claim_text,
            "people": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "years": [],
            "numbers": [],
            "percentages": [],
            "products": [],
            "quoted_phrases": [],
            "key_tokens": [],
        }
        if not claim_text.strip():
            return result

        # 0. Extract Exact Quoted Phrases or Lyric Lines
        lyric_lines = re.findall(r"(?:♪\s*|\"\s*)([^♪\"\r\n]{6,})(?:♪|\"|\r|\n|$)", claim_text)
        for line in lyric_lines:
            clean_line = line.strip()
            if len(clean_line.split()) >= 3 and clean_line not in result["quoted_phrases"]:
                result["quoted_phrases"].append(clean_line)

        # 1. Percentages and Quantities Regex
        percentages = re.findall(r"\b\d+(?:\.\d+)?%", claim_text)
        result["percentages"] = list(set(percentages))

        # 2. Product / Code Name Regex (e.g., vaccine X, COVID-19, Europa Clipper)
        products = re.findall(r"\b(?:vaccine\s+[A-Z0-9]+|[A-Z][a-z]+ [A-Z][a-z]+ (?:spacecraft|mission|probe|rover)|[A-Z0-9]+-[A-Z0-9]+)\b", claim_text, re.I)
        result["products"] = list(set(products))

        # 3. Location Regex Fallback
        known_locs = re.findall(r"\b(India|US|USA|UK|China|Russia|Germany|France|Japan|Brazil|Europe|Africa|Asia|London|Washington|California)\b", claim_text, re.I)
        result["locations"] = list(set([loc.capitalize() for loc in known_locs]))

        # 4. Primary NER & Linguistic Analysis via spaCy
        if HAS_SPACY and nlp_spacy:
            try:
                doc = nlp_spacy(claim_text[:2000])
                for ent in doc.ents:
                    val = ent.text.strip()
                    if len(val) < 2:
                        continue
                    if ent.label_ == "PERSON" and val not in result["people"]:
                        result["people"].append(val)
                    elif ent.label_ in ("ORG", "ORGANIZATION") and val not in result["organizations"]:
                        result["organizations"].append(val)
                    elif ent.label_ in ("GPE", "LOC", "LOCATION") and val not in result["locations"]:
                        result["locations"].append(val)
                    elif ent.label_ == "DATE" and val not in result["dates"]:
                        result["dates"].append(val)
                    elif ent.label_ == "CARDINAL" and val not in result["numbers"]:
                        result["numbers"].append(val)

                # Extract key noun chunks & verbs
                for token in doc:
                    if token.is_alpha and not token.is_stop and len(token.text) > 2:
                        if token.pos_ in ("NOUN", "PROPN", "VERB") and token.text.lower() not in result["key_tokens"]:
                            result["key_tokens"].append(token.text.lower())
            except Exception as e:
                log.warning(f"[ClaimParser] spaCy parsing exception: {e}")

        # 5. Fallback Regex for Known Organizations (WHO, NASA, UN, CDC, FDA)
        org_matches = re.findall(r"\b(WHO|NASA|UN|CDC|FDA|FBI|CIA|EU|ISRO|ESA|UNESCO|UNICEF)\b", claim_text)
        for org in org_matches:
            if org not in result["organizations"]:
                result["organizations"].append(org)

        year_matches = re.findall(r"\b(19\d\d|20\d\d)\b", claim_text)
        result["years"] = list(set(year_matches))

        date_matches = re.findall(
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b", claim_text, re.I
        )
        for d in date_matches:
            if d not in result["dates"]:
                result["dates"].append(d)

        # Fallback key token extraction if spaCy was unavailable
        if not result["key_tokens"]:
            words = re.findall(r"\b[a-zA-Z]{3,}\b", claim_text.lower())
            stopwords = {"the", "and", "for", "that", "this", "with", "from", "was", "were", "been", "have", "has", "had", "says", "said"}
            result["key_tokens"] = [w for w in words if w not in stopwords][:10]

        return result

    def classify_claim_type(self, structured_claim: Dict[str, Any]) -> str:
        """Categorize input into HEALTH_STATISTIC, SCIENCE_SPACE, CULTURE_LYRICS, or POLITICS_NEWS."""
        if structured_claim.get("quoted_phrases") or bool(re.search(r"[♪♫]", structured_claim.get("text", ""))):
            return "CULTURE_LYRICS"
        if structured_claim.get("percentages") or "vaccine" in structured_claim.get("text", "").lower() or "who" in [o.lower() for o in structured_claim.get("organizations", [])]:
            return "HEALTH_STATISTIC"
        if structured_claim.get("products") or "spacecraft" in structured_claim.get("text", "").lower() or "nasa" in [o.lower() for o in structured_claim.get("organizations", [])]:
            return "SCIENCE_SPACE"
        return "POLITICS_NEWS"

    def score_query_quality(self, query: str, structured_claim: Dict[str, Any]) -> float:
        """
        Normalized Query Quality Scoring Engine v3.5 (0.0 to 100.0%)
        Applies claim-type specific weighting so scores across different domains are directly comparable.
        """
        claim_type = self.classify_claim_type(structured_claim)
        score = 0.0
        q_lower = query.lower()

        if claim_type == "CULTURE_LYRICS":
            # Weighting: Quoted Phrase (50%), Lyrics Keyword (30%), Phrase Length (20%)
            for phrase in structured_claim.get("quoted_phrases", []):
                if f'"{phrase.lower()}"' in q_lower or phrase.lower() in q_lower:
                    score += 50.0
            if "lyrics" in q_lower or "song" in q_lower or "artist" in q_lower:
                score += 30.0
            if len(query.split()) >= 4:
                score += 20.0

        elif claim_type == "HEALTH_STATISTIC":
            # Weighting: Percentage (30%), Organization (25%), Location (25%), Year/Date (20%)
            for pct in structured_claim.get("percentages", []):
                if pct.lower() in q_lower: score += 30.0
            for org in structured_claim.get("organizations", []):
                if org.lower() in q_lower: score += 25.0
            for loc in structured_claim.get("locations", []):
                if loc.lower() in q_lower: score += 25.0
            for year in structured_claim.get("years", []) + structured_claim.get("dates", []):
                if year.lower() in q_lower: score += 20.0

        elif claim_type == "SCIENCE_SPACE":
            # Weighting: Product/Mission (35%), Organization (30%), Year/Date (20%), Location (15%)
            for prod in structured_claim.get("products", []):
                if prod.lower() in q_lower: score += 35.0
            for org in structured_claim.get("organizations", []):
                if org.lower() in q_lower: score += 30.0
            for year in structured_claim.get("years", []) + structured_claim.get("dates", []):
                if year.lower() in q_lower: score += 20.0
            for loc in structured_claim.get("locations", []):
                if loc.lower() in q_lower: score += 15.0

        else: # POLITICS_NEWS
            # Weighting: Person/Org (35% capped), Location (25%), Date (20%), Keywords (20%)
            # EDGE-03 FIX: Cap the per-category entity contribution at 35 points.
            # Without the cap, 3 orgs would score 105 (over 100) and tie with 2-org claims at 100%,
            # destroying the ranking signal for genuinely higher-quality queries.
            entity_score = min(35.0, sum(
                35.0 for ent in structured_claim.get("organizations", []) + structured_claim.get("people", [])
                if ent.lower() in q_lower
            ))
            score += entity_score
            for loc in structured_claim.get("locations", []):
                if loc.lower() in q_lower: score += 25.0
            for year in structured_claim.get("years", []) + structured_claim.get("dates", []):
                if year.lower() in q_lower: score += 20.0
            if "fact check" in q_lower: score += 20.0

        # Trailing Preposition Penalty
        tokens = query.split()
        if tokens and tokens[-1].lower() in {"in", "by", "for", "to", "at", "with", "of", "the", "a", "an"}:
            score -= 15.0

        return min(100.0, max(0.0, score))

    def generate_expanded_queries(self, raw_input: str) -> List[str]:
        """
        Structured Query Expansion Engine v3.5
        Applies Entity Linking, Claim Classification, and Normalized Query Scoring.
        """
        from app.services.tier4.entity_resolver import entity_resolver

        has_musical_notes = bool(re.search(r"[♪♫]", raw_input))
        cleaned = re.sub(r"[♪♫\r\n\t]+", " ", raw_input).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)

        # 1. Structured Claim & Entity Linking
        parsed = self.parse_claim(raw_input if has_musical_notes else cleaned)
        linked = entity_resolver.resolve_entities(raw_input)
        
        quoted_phrases = parsed.get("quoted_phrases", [])
        orgs = parsed.get("organizations", [])
        people = parsed.get("people", [])
        locs = parsed.get("locations", [])
        percentages = parsed.get("percentages", [])
        products = parsed.get("products", [])
        years = parsed.get("years", [])
        dates = parsed.get("dates", [])

        # Include high confidence entities (confidence >= 0.70) from probabilistic entity resolver
        clean_entities = list(dict.fromkeys(orgs + people + locs + products + linked.get("high_confidence_entities", [])))

        generic = {"unknown", "title", "youtube", "video", "channel", "subscribe", "like"}
        clean_entities = [e for e in clean_entities if e.lower() not in generic]

        candidate_queries = []

        # ── Case A: Exact Lyric / Quoted Line Detection ──
        if quoted_phrases:
            for phrase in quoted_phrases[:2]:
                candidate_queries.append(f'"{phrase}" song lyrics')
                candidate_queries.append(f'"{phrase}" artist title')
                candidate_queries.append(f'"{phrase}" fact check')

        # ── Case B: Factual & Quantitative News Claims ──
        words = [w for w in re.findall(r"\b[A-Za-z0-9%°\.-]{2,}\b", cleaned) if w.lower() not in generic]
        while words and words[-1].lower() in {"in", "by", "for", "to", "at", "with", "of", "the", "a", "an"}:
            words.pop()
        
        if words:
            candidate_queries.append(" ".join(words[:12]))

        # Entity + Quantity + Location Targeted Query
        q2_parts = list(dict.fromkeys(clean_entities + percentages + locs + dates + years))
        if q2_parts:
            candidate_queries.append(f"{' '.join(q2_parts)} fact check")

        # Entity Resolver Enriched Query
        if linked.get("entity_aliases"):
            candidate_queries.append(f"{' '.join(linked['entity_aliases'])} {' '.join(percentages + locs)} fact check".strip())

        # Fallback
        if not candidate_queries:
            candidate_queries.append(cleaned[:120])

        unique_candidates = list(dict.fromkeys([q.strip() for q in candidate_queries if q.strip()]))

        # Rank candidates using Normalized Claim-Type Quality Score
        scored_candidates = []
        for q in unique_candidates:
            score = self.score_query_quality(q, parsed)
            scored_candidates.append((score, q))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        ranked_queries = [q for _, q in scored_candidates]

        log.info(f"[ClaimParser] Claim Type: '{self.classify_claim_type(parsed)}' | Ranked {len(ranked_queries)} queries (Top score: {scored_candidates[0][0] if scored_candidates else 0.0:.1f}%)")
        return ranked_queries[:4]

    def rewrite_query_for_search(self, raw_input: str) -> str:
        """Backward compatibility wrapper returning highest scored query."""
        expanded = self.generate_expanded_queries(raw_input)
        return expanded[0] if expanded else raw_input[:150]


claim_parser = ClaimParser()
