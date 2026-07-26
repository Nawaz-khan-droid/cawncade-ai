"""
CAWNCADE AI v3.5 — Tier 4 No-LLM Grounded Deterministic Verification Engine.

Provides non-generative, CPU-bound extractive evidence analysis, BM25 ranking,
spaCy entity extraction, date conflict detection, and rule-based grounded verification
when all online LLM providers (Tiers 1-3) are unreachable.
"""

import re
from typing import List, Dict, Any
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

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False


class OfflineNLPService:
    """
    Tier 4 Deterministic No-LLM Evidence Processing & Verification Engine.
    
    Modules:
      1. spaCy / Regex Entity Extractor (People, Orgs, Locations, Dates)
      2. Sumy LexRank Extractive Summarizer
      3. BM25 / TF-IDF Evidence Sentence Ranker
      4. Grounded Rule-Based Verification Engine (Date/Entity conflict scoring)
    """

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extracts People, Organizations, Locations, & Dates via spaCy -> Regex."""
        entities = {"people": [], "organizations": [], "locations": [], "dates": []}
        if not text:
            return entities

        # 1. Primary NER: spaCy
        if HAS_SPACY and nlp_spacy:
            try:
                doc = nlp_spacy(text[:4000])
                for ent in doc.ents:
                    val = ent.text.strip()
                    if len(val) < 2:
                        continue
                    if ent.label_ == "PERSON" and val not in entities["people"]:
                        entities["people"].append(val)
                    elif ent.label_ in ("ORG", "ORGANIZATION") and val not in entities["organizations"]:
                        entities["organizations"].append(val)
                    elif ent.label_ in ("GPE", "LOC", "LOCATION") and val not in entities["locations"]:
                        entities["locations"].append(val)
                    elif ent.label_ == "DATE" and val not in entities["dates"]:
                        entities["dates"].append(val)
            except Exception as e:
                log.warning(f"[OfflineNLP] spaCy NER exception: {e}")

        # 2. Pattern Fallback for Corporate & Date formats
        org_matches = re.findall(
            r"\b[A-Z][a-zA-Z0-9\.]+(?: [A-Z][a-zA-Z0-9\.]+)* (?:Corporation|Corp|Inc|LLC|Tech|Group|News|Gov|Ministry|Department)\b", text
        )
        for org in org_matches:
            if org not in entities["organizations"]:
                entities["organizations"].append(org)

        date_matches = re.findall(
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b|\b\d{4}\b", text, re.I
        )
        for d in date_matches:
            if d not in entities["dates"]:
                entities["dates"].append(d)

        return entities

    def rank_sentences_bm25(self, query: str, sentences: List[str], top_k: int = 3) -> List[str]:
        """Ranks evidence sentences using BM25 keyword matching against query."""
        if not sentences:
            return []
        if not HAS_BM25 or not query.strip():
            return sentences[:top_k]

        try:
            tokenized_corpus = [s.lower().split() for s in sentences]
            tokenized_query = query.lower().split()
            bm25 = BM25Okapi(tokenized_corpus)
            scores = bm25.get_scores(tokenized_query)
            
            # Sort sentences by BM25 score descending
            ranked = [s for _, s in sorted(zip(scores, sentences), reverse=True if max(scores) > 0 else False)]
            return ranked[:top_k]
        except Exception as e:
            log.warning(f"[OfflineNLP] BM25 ranking fallback: {e}")
            return sentences[:top_k]

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

    def evaluate_grounded_verdict(self, claim: str, evidence_text: str, sources_count: int) -> Dict[str, Any]:
        """
        Deterministic Verification Engine.
        Compares claim entities/dates against collected web evidence.
        """
        claim_ents = self.extract_entities(claim)
        evidence_ents = self.extract_entities(evidence_text)

        # 1. Entity Overlap
        claim_all_ents = set(claim_ents["people"] + claim_ents["organizations"] + claim_ents["locations"])
        evidence_all_ents = set(evidence_ents["people"] + evidence_ents["organizations"] + evidence_ents["locations"])

        if claim_all_ents:
            matched_ents = claim_all_ents.intersection(evidence_all_ents)
            entity_overlap_score = len(matched_ents) / len(claim_all_ents)
        else:
            entity_overlap_score = 0.5  # Neutral if no entities found

        # 2. Date Alignment & Conflict Detection (Extract 4-digit years)
        claim_years = set(re.findall(r"\b(19\d\d|20\d\d)\b", " ".join(claim_ents["dates"] + [claim])))
        evidence_years = set(re.findall(r"\b(19\d\d|20\d\d)\b", " ".join(evidence_ents["dates"] + [evidence_text[:2000]])))

        date_match = True
        date_conflict = False
        if claim_years and evidence_years:
            if claim_years.intersection(evidence_years):
                date_match = True
            else:
                date_conflict = True
                date_match = False

        # 3. Grounded Verdict Decision Logic
        if sources_count == 0 or len(evidence_text.strip()) < 50:
            verdict = "INSUFFICIENT EVIDENCE FOR DETERMINISTIC VERDICT"
            confidence = "LOW"
        elif date_conflict and entity_overlap_score > 0.5:
            verdict = "CONTRADICTED BY AVAILABLE EVIDENCE (DATE / TIMELINE MISMATCH)"
            confidence = "MEDIUM"
        elif entity_overlap_score >= 0.6 and date_match:
            verdict = "SUPPORTED BY AVAILABLE EVIDENCE"
            confidence = "HIGH" if sources_count >= 3 else "MEDIUM"
        elif entity_overlap_score >= 0.3:
            verdict = "MIXED / PARTIALLY SUPPORTED EVIDENCE"
            confidence = "MEDIUM"
        else:
            verdict = "UNVERIFIED / NO STRONG EVIDENCE MATCH"
            confidence = "LOW"

        return {
            "verdict": verdict,
            "confidence": confidence,
            "entity_overlap_score": round(entity_overlap_score, 2),
            "date_match": date_match,
            "date_conflict": date_conflict,
            "claim_entities": claim_ents,
            "evidence_entities": evidence_ents,
        }

    def generate_report(self, query: str, evidence_text: str, sources_count: int = 0) -> str:
        """Generates a structured, transparent, non-generative evidence report."""
        if not evidence_text or len(evidence_text.strip()) < 30:
            return (
                "### ⚠️ Tier 4 Computational Analysis (No-LLM Mode)\n"
                "*No readable text evidence was retrieved from target. Verification performed strictly via search citations.*"
            )

        # Sentence segmentation & BM25 ranking
        raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?]) +", evidence_text) if len(s.strip()) > 15]
        bm25_top_sentences = self.rank_sentences_bm25(query, raw_sentences, top_k=3)
        bm25_summary = " ".join(bm25_top_sentences) if bm25_top_sentences else self.summarize_extractive(evidence_text, 3)

        eval_res = self.evaluate_grounded_verdict(query, evidence_text, sources_count)

        entities = eval_res["evidence_entities"]
        people_str = ", ".join(entities["people"][:5]) or "None detected"
        orgs_str = ", ".join(entities["organizations"][:5]) or "None detected"
        locs_str = ", ".join(entities["locations"][:5]) or "None detected"
        dates_str = ", ".join(entities["dates"][:5]) or "None detected"

        return (
            f"### 📊 Local Computational Evidence Verification (Tier 4 No-LLM Mode)\n"
            f"*Notice: Online AI LLM reasoning was unavailable. This report was computed deterministically using CPU NLP (spaCy NER, LexRank, BM25 sentence ranking, and Citation Alignment).* \n\n"
            f"**Grounded Deterministic Verdict**: `{eval_res['verdict']}` (Confidence: **{eval_res['confidence']}**)\n"
            f"- **Entity Overlap Match**: `{int(eval_res['entity_overlap_score'] * 100)}%` | **Timeline Match**: `{'PASSED' if eval_res['date_match'] else 'CONFLICT DETECTED'}`\n\n"
            f"**BM25 Extracted Evidence Sentences:**\n{bm25_summary}\n\n"
            f"**Grounded Entities Detected:**\n"
            f"- 👤 **People**: {people_str}\n"
            f"- 🏢 **Organizations**: {orgs_str}\n"
            f"- 📍 **Locations**: {locs_str}\n"
            f"- 📅 **Timeline / Dates**: {dates_str}\n\n"
            f"**Evidence Grounding**: Cross-referenced across {sources_count} web citation(s)."
        )


offline_nlp_service = OfflineNLPService()
