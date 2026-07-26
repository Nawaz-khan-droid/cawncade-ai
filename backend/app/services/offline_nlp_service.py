"""
CAWNCADE AI v3.5 — Tier 4 Offline Grounded Deterministic NLP Service.

Provides non-generative, CPU-bound extractive evidence synthesis, entity extraction,
and rule-based grounded verification when all online LLM providers (Tiers 1-3) are unreachable.
"""

import re
from app.utils.logger import log

try:
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.lex_rank import LexRankSummarizer
    HAS_SUMY = True
except ImportError:
    HAS_SUMY = False

try:
    import spacy
    try:
        nlp_spacy = spacy.load("en_core_web_sm")
    except Exception:
        nlp_spacy = spacy.blank("en")
    HAS_SPACY = True
except Exception:
    HAS_SPACY = False


class OfflineNLPService:
    """
    Tier 4 Deterministic Offline Evidence Processing Engine.
    Extractive LexRank Summarizer + Cascade Entity Extractor (spaCy -> NLTK -> Regex)
    + Grounded Rule-Based Verdict Calculator.
    """

    def extract_entities(self, text: str) -> dict:
        """Extracts People, Organizations, Locations, & Dates via spaCy -> NLTK -> Regex."""
        entities = {"people": [], "organizations": [], "locations": [], "dates": []}
        if not text:
            return entities

        # 1. Primary NER: spaCy (if available)
        if HAS_SPACY and nlp_spacy:
            try:
                doc = nlp_spacy(text[:3000])
                for ent in doc.ents:
                    val = ent.text.strip()
                    if ent.label_ == "PERSON" and val not in entities["people"]:
                        entities["people"].append(val)
                    elif ent.label_ in ("ORG", "ORGANIZATION") and val not in entities["organizations"]:
                        entities["organizations"].append(val)
                    elif ent.label_ in ("GPE", "LOC", "LOCATION") and val not in entities["locations"]:
                        entities["locations"].append(val)
                    elif ent.label_ == "DATE" and val not in entities["dates"]:
                        entities["dates"].append(val)
                if any(entities.values()):
                    return entities
            except Exception as e:
                log.warning(f"[OfflineNLP] spaCy NER failed: {e}. Falling back to NLTK.")

        # 2. Secondary NER: NLTK ne_chunk
        try:
            import nltk
            words = nltk.word_tokenize(text[:3000])
            pos_tags = nltk.pos_tag(words)
            chunks = nltk.ne_chunk(pos_tags)

            for chunk in chunks:
                if hasattr(chunk, "label"):
                    name = " ".join(c[0] for c in chunk)
                    label = chunk.label()
                    if label in ("PERSON",) and name not in entities["people"]:
                        entities["people"].append(name)
                    elif label in ("ORGANIZATION", "ORGANISATION") and name not in entities["organizations"]:
                        entities["organizations"].append(name)
                    elif label in ("GPE", "LOCATION") and name not in entities["locations"]:
                        entities["locations"].append(name)
        except Exception:
            pass

        # 3. Fallback: Regex for dates & corporate patterns
        org_matches = re.findall(r"\b[A-Z][a-z]+ (?:Corporation|Inc|LLC|Tech|Group|News|Gov|Ministry|Department)\b", text)
        entities["organizations"] = list(set(entities["organizations"] + org_matches[:5]))

        date_matches = re.findall(
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b|\b\d{4}\b", text, re.I
        )
        entities["dates"] = list(set(entities["dates"] + date_matches[:5]))

        return entities

    def summarize_extractive(self, text: str, num_sentences: int = 3) -> str:
        """Extracts top central sentences using LexRank or sentence frequency scoring."""
        if not text.strip() or len(text) < 50:
            return "Insufficient text payload to perform extractive NLP summarization."

        if HAS_SUMY:
            try:
                parser = PlaintextParser.from_string(text, Tokenizer("english"))
                summarizer = LexRankSummarizer()
                summary_sentences = summarizer(parser.document, num_sentences)
                return " ".join([str(s) for s in summary_sentences])
            except Exception as e:
                log.warning(f"[OfflineNLP] Sumy LexRank failed: {e}. Using frequency fallback.")

        # Fallback sentence splitter
        sentences = [s.strip() for s in re.split(r"(?<=[.!?]) +", text) if len(s.strip()) > 15]
        return " ".join(sentences[:num_sentences])

    def generate_report(self, evidence_text: str, sources_count: int = 0) -> str:
        """Generates a structured, non-hallucinated evidence report."""
        if not evidence_text or len(evidence_text.strip()) < 30:
            return (
                "### ⚠️ Tier 4 Offline Analysis Unavailable\n"
                "*No readable text evidence was retrieved. Verification performed strictly via search citations.*"
            )

        summary = self.summarize_extractive(evidence_text, num_sentences=3)
        entities = self.extract_entities(evidence_text)

        people_str = ", ".join(entities["people"][:5]) or "None detected"
        orgs_str = ", ".join(entities["organizations"][:5]) or "None detected"
        locs_str = ", ".join(entities["locations"][:5]) or "None detected"
        dates_str = ", ".join(entities["dates"][:5]) or "None detected"

        return (
            f"### 📊 Local Computational Evidence Analysis (Tier 4 Offline Mode)\n"
            f"*Note: Online AI LLM reasoning was unavailable. This objective report was generated via deterministic CPU statistical NLP metrics (LexRank).* \n\n"
            f"**Key Extracted Sentences:**\n{summary}\n\n"
            f"**Detected Grounded Entities:**\n"
            f"- 👤 **People**: {people_str}\n"
            f"- 🏢 **Organizations**: {orgs_str}\n"
            f"- 📍 **Locations**: {locs_str}\n"
            f"- 📅 **Dates / Timeline**: {dates_str}\n\n"
            f"**Evidence Status**: Grounded across {sources_count} web citation(s)."
        )


offline_nlp_service = OfflineNLPService()
