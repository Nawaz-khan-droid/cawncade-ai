"""
Content Extraction Module.
Handles extraction of text content from URLs and raw HTML.
"""
import re
import httpx
from bs4 import BeautifulSoup
from app.utils.logger import log
from ...config.settings import get_settings

settings = get_settings()


class ContentExtractor:
    """Extract clean text content from URLs."""

    def __init__(self):
        self.timeout = settings.WEB_FETCH_TIMEOUT
        self.user_agent = (
            "Mozilla/5.0 (compatible; CAWNCADE-AI/0.1; +https://cawncade.ai/bot)"
        )

    async def extract_from_url(self, url: str) -> dict:
        """
        Extract title, clean text, and metadata from a URL.
        Returns dict with keys: title, text, url, word_count, extracted_at
        """
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text

            return self._parse_html(html, url)

        except httpx.TimeoutException:
            log.warning(f"Timeout extracting content from: {url}")
            return {"url": url, "title": "", "text": "", "error": "timeout"}
        except httpx.HTTPStatusError as e:
            log.warning(f"HTTP {e.response.status_code} for: {url}")
            return {"url": url, "title": "", "text": "", "error": f"http_{e.response.status_code}"}
        except Exception as e:
            log.error(f"Extraction error for {url}: {e}")
            return {"url": url, "title": "", "text": "", "error": str(e)}

    def _parse_html(self, html: str, url: str) -> dict:
        """Parse HTML into structured content."""
        soup = BeautifulSoup(html, "lxml")

        # Remove unwanted tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
            tag.decompose()

        # Extract title
        title = ""
        if soup.title:
            title = soup.title.get_text(strip=True)

        # Try common article containers
        article = (
            soup.find("article")
            or soup.find("main")
            or soup.find(class_=re.compile(r"article|post|content|story|entry", re.I))
            or soup.find(id=re.compile(r"article|post|content|story|entry", re.I))
        )

        if article:
            text = article.get_text(separator=" ", strip=True)
        else:
            # Fallback: use body
            body = soup.find("body")
            text = body.get_text(separator=" ", strip=True) if body else ""

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()
        word_count = len(text.split())

        # Extract meta description
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag:
            meta_desc = meta_tag.get("content", "")

        return {
            "url": url,
            "title": title,
            "text": text[:10000],  # Cap at 10k chars to prevent LLM context overflow
            "meta_description": meta_desc,
            "word_count": word_count,
            "extracted_at": None,  # Will be set by caller
        }

    def extract_keywords(self, text: str, top_n: int = 10) -> list[str]:
        """
        Simple keyword extraction using TF frequency.
        Used as a lightweight alternative when TF-IDF model is not available.
        """
        from sklearn.feature_extraction.text import TfidfVectorizer

        stop_words = "english"
        try:
            vectorizer = TfidfVectorizer(stop_words=stop_words, max_features=top_n, token_pattern=r"(?u)\b[a-z]{3,}\b")
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]

            # Sort by score descending
            keywords_with_scores = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
            return [kw for kw, score in keywords_with_scores if score > 0][:top_n]
        except Exception as e:
            log.error(f"Keyword extraction failed: {e}")
            return []


# Singleton
content_extractor = ContentExtractor()
