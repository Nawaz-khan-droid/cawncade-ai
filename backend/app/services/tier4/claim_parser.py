"""
CAWNCADE AI v3.5 — Tier 4 Claim Decomposition Parser.
Decomposes user claims into structured subjects, actions, dates, numbers, and entities.
"""

import re
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
    """Decomposes text claims into structured linguistic components for deterministic verification."""

    def parse_claim(self, claim_text: str) -> Dict[str, Any]:
        result = {
            "text": claim_text,
            "people": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "years": [],
            "numbers": [],
            "key_tokens": [],
        }
        if not claim_text.strip():
            return result

        # 1. Primary NER & Linguistic Analysis via spaCy
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

        # 2. Pattern Fallback for Corporate Suffixes, Years, and Quantities
        org_matches = re.findall(
            r"\b[A-Z][a-zA-Z0-9\.]+(?: [A-Z][a-zA-Z0-9\.]+)* (?:Corporation|Corp|Inc|LLC|Tech|Group|News|Gov|Ministry|Department)\b",
            claim_text,
        )
        for org in org_matches:
            if org not in result["organizations"]:
                result["organizations"].append(org)

        year_matches = re.findall(r"\b(19\d\d|20\d\d)\b", claim_text)
        result["years"] = list(set(year_matches))

        date_matches = re.findall(
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b", claim_text, re.I
        )
        for d in date_matches:
            if d not in result["dates"]:
                result["dates"].append(d)

        # Fallback key token extraction if spaCy was unavailable
        if not result["key_tokens"]:
            words = re.findall(r"\b[a-zA-Z]{3,}\b", claim_text.lower())
            stopwords = {"the", "and", "for", "that", "this", "with", "from", "was", "were", "been", "have", "has", "had"}
            result["key_tokens"] = [w for w in words if w not in stopwords][:10]

        return result


claim_parser = ClaimParser()
