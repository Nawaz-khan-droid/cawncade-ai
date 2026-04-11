"""
Content Extraction Module v3.0.
Fetches URLs with realistic browser User-Agent and proxy support.
Extracts article title, text, and generates search keywords.
"""

import re
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from app.config.settings import get_settings
from app.utils.logger import log

settings = get_settings()


class ContentExtractor:
    def __init__(self):
        self.timeout = settings.WEB_FETCH_TIMEOUT
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def extract_from_url(self, url: str) -> dict:
        result = {"title": "", "text": "", "keywords": "", "success": False, "original_url": url}

        try:
            client_kwargs = {"timeout": self.timeout, "follow_redirects": True, "headers": self.headers}
            if settings.WEBSHARE_PROXY_URL:
                client_kwargs["proxy"] = settings.WEBSHARE_PROXY_URL

            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(url)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            title = (
                (soup.find("meta", property="og:title") and soup.find("meta", property="og:title").get("content", ""))
                or (soup.find("meta", name="twitter:title") and soup.find("meta", name="twitter:title").get("content", ""))
                or (soup.find("title") and soup.find("title").get_text(strip=True))
                or ""
            )

            result["title"] = self._clean_text(title)

            article_tag = (
                soup.find("article") or soup.find("main")
                or soup.find("div", class_=re.compile(r"article|content|story|post", re.I))
                or soup.find("body")
            )

            if article_tag:
                for tag in article_tag.find_all(["script", "style", "nav", "footer", "aside", "header"]):
                    tag.decompose()
                text = article_tag.get_text(separator=" ", strip=True)
                result["text"] = self._clean_text(text)

            result["keywords"] = self._extract_keywords(result["title"], result["text"])
            if result["title"] or result["keywords"]:
                result["success"] = True
                log.info(f"[Extractor] Extracted: '{result['title'][:80]}'")
            else:
                log.warning(f"[Extractor] No content found at {url}")

        except httpx.TimeoutException:
            log.warning(f"[Extractor] Timeout: {url}")
            result["keywords"] = self.extract_keywords_from_url(url)
            if result["keywords"]:
                result["success"] = True
        except httpx.HTTPStatusError as e:
            log.error(f"[Extractor] HTTP {e.response.status_code}: {url}")
            result["keywords"] = self.extract_keywords_from_url(url)
            if result["keywords"]:
                result["success"] = True
        except Exception as e:
            log.error(f"[Extractor] Error: {url}: {e}")
            result["keywords"] = self.extract_keywords_from_url(url)
            if result["keywords"]:
                result["success"] = True

        return result

    def extract_keywords(self, text: str, top_n: int = 10) -> list:
        from sklearn.feature_extraction.text import TfidfVectorizer
        try:
            vectorizer = TfidfVectorizer(stop_words="english", max_features=top_n, token_pattern=r"(?u)\b[a-z]{3,}\b")
            tfidf_matrix = vectorizer.fit_transform([text])
            feature_names = vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            keywords = sorted(zip(feature_names, scores), key=lambda x: x[1], reverse=True)
            return [kw for kw, score in keywords if score > 0][:top_n]
        except Exception:
            return []

    def extract_keywords_from_url(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            path = unquote(parsed.path)
            path = re.sub(r"^(/en-in|/en|/news|/article|/story|/world|/india)+", "", path, flags=re.I)
            path = re.sub(r"\.(html|htm|php|asp|aspx)$", "", path, flags=re.I)
            words = re.split(r"[-/]", path)
            stop_words = {"en", "in", "news", "article", "story", "world", "india", "the", "a", "an", "ar", "aa", "bb", "cc", "com", "www", "http", "https"}
            meaningful = [w for w in words if len(w) > 2 and w.lower() not in stop_words]
            return " ".join(meaningful[:10]) if meaningful else ""
        except Exception:
            return ""

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text)
        text = text.replace("\xa0", " ")
        return text.strip()

    def _extract_keywords(self, title: str, text: str) -> str:
        if title:
            clean_title = re.split(r"\s*[-|]\s*(MSN|BBC|CNN|Reuters|NDTV|Times of India|Hindustan Times|Google News)\b", title, flags=re.I)[0]
            clean_title = self._clean_text(clean_title)
            if len(clean_title) > 5:
                return clean_title
        if text:
            snippet = text[:200]
            filler_pattern = r"\b(is|are|was|were|be|been|have|has|had|do|does|did|will|would|could|should|the|a|an|of|in|for|on|with|at|by|from|to|and|or|but|if|this|that)\b"
            cleaned = re.sub(filler_pattern, "", snippet, flags=re.I)
            cleaned = self._clean_text(cleaned)
            if len(cleaned) > 10:
                return cleaned[:120]
        return ""

    def is_url(self, text: str) -> bool:
        return bool(re.match(r"^https?://\S+$", text.strip()))


content_extractor = ContentExtractor()
