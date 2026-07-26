"""
CAWNCADE AI v3.5 — Tier 4 Extractive LexRank Summarizer.
Extracts top central sentences from evidence via graph similarity.
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


class ExtractiveSummarizer:
    """Extracts central sentences via Sumy LexRank algorithm."""

    def summarize(self, text: str, num_sentences: int = 3) -> str:
        if not text.strip() or len(text) < 50:
            return "Insufficient text payload to perform extractive NLP summarization."

        if HAS_SUMY:
            try:
                parser = PlaintextParser.from_string(text, Tokenizer("english"))
                summarizer = LexRankSummarizer()
                summary_sentences = summarizer(parser.document, num_sentences)
                return " ".join([str(s) for s in summary_sentences])
            except Exception as e:
                log.warning(f"[ExtractiveSummarizer] Sumy LexRank failed: {e}. Using frequency fallback.")

        # Sentence splitter fallback
        sentences = [s.strip() for s in re.split(r"(?<=[.!?]) +", text) if len(s.strip()) > 15]
        return " ".join(sentences[:num_sentences])


extractive_summarizer = ExtractiveSummarizer()
