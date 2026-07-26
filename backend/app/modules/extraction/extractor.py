"""
Content Extraction Module v3.0.
Fetches URLs with realistic browser User-Agent.
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
        result = {
            "title": "",
            "text": "",
            "keywords": "",
            "success": False,
            "extraction_status": "FAILED",
            "fallback_used": False,
            "original_url": url,
        }

        # SSRF Security Guard Check
        from app.services.safe_browsing_service import is_ssrf_safe_url
        is_safe, error_reason = is_ssrf_safe_url(url)
        if not is_safe:
            log.warning(f"[Extractor] {error_reason} Target: {url}")
            result["error"] = error_reason
            result["keywords"] = self.extract_keywords_from_url(url)
            return result

        # ── PRIMARY PATH: Jina Reader API ──
        try:
            jina_url = f"https://r.jina.ai/{url}"
            jina_headers = {
                "User-Agent": self.headers["User-Agent"],
                "Accept": "text/event-stream, text/plain, */*",
                "X-No-Cache": "true",
            }
            timeout = getattr(settings, "JINA_READER_TIMEOUT", 15)

            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                jina_resp = await client.get(jina_url, headers=jina_headers)
                if jina_resp.status_code == 200:
                    raw_jina_text = jina_resp.text
                    cleaned_jina = self._clean_text(raw_jina_text)
                    
                    # Quality Gate: Valid article length check (>1,000 chars)
                    if len(cleaned_jina) >= 1000:
                        lines = [line.strip() for line in cleaned_jina.split("\n") if line.strip()]
                        result["title"] = lines[0][:200] if lines else self.extract_keywords_from_url(url)
                        result["text"] = self._apply_3way_compression(cleaned_jina)
                        result["keywords"] = self._extract_keywords(result["title"], result["text"])
                        result["success"] = True
                        result["extraction_status"] = "SUCCESS"
                        result["method"] = "jina_reader"
                        log.info(f"[Extractor] 🚀 Jina Reader SUCCESS: '{result['title'][:60]}' ({len(result['text'])} chars)")
                        return result
        except Exception as jina_err:
            log.info(f"[Extractor] Jina Reader bypassed/failed ({jina_err}). Engaging httpx + BeautifulSoup fallback.")

        # ── SECONDARY FALLBACK PATH: Local httpx + BeautifulSoup ──
        result["fallback_used"] = True
        try:
            client_kwargs = {"timeout": self.timeout, "follow_redirects": True, "headers": self.headers}
            max_bytes = getattr(settings, "MAX_RESPONSE_BYTES", 5242880)

            async with httpx.AsyncClient(**client_kwargs) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()
                    
                    # 5MB Response Byte Limit Safeguard
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > max_bytes:
                        log.warning(f"[Extractor] Aborted fetching: Content-Length ({content_length}) exceeds 5MB limit.")
                        result["keywords"] = self.extract_keywords_from_url(url)
                        result["text"] = "URL response size exceeded 5MB threshold. Web search citations will be used for verification."
                        return result

                    chunks = []
                    downloaded = 0
                    async for chunk in response.aiter_bytes():
                        downloaded += len(chunk)
                        if downloaded > max_bytes:
                            log.warning(f"[Extractor] Aborted fetching: Download size exceeded 5MB cap.")
                            result["keywords"] = self.extract_keywords_from_url(url)
                            result["text"] = "URL response body exceeded 5MB limit. Web search citations will be used for verification."
                            return result
                        chunks.append(chunk)

                    html_content = b"".join(chunks).decode("utf-8", errors="ignore")

            soup = BeautifulSoup(html_content, "lxml")

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
                cleaned_text = self._clean_text(text)
                result["text"] = self._apply_3way_compression(cleaned_text)

            result["keywords"] = self._extract_keywords(result["title"], result["text"])
            if result["title"] or result["keywords"]:
                result["success"] = True
                result["extraction_status"] = "SUCCESS"
                result["method"] = "beautifulsoup_fallback"
                log.info(f"[Extractor] BeautifulSoup Fallback SUCCESS: '{result['title'][:60]}'")
            else:
                log.warning(f"[Extractor] No content found at {url}")
                result["text"] = "Unable to extract main article text due to access restrictions or client-side rendering. Web search citations will be used for verification."

        except httpx.TimeoutException:
            log.warning(f"[Extractor] Timeout: {url}")
            result["keywords"] = self.extract_keywords_from_url(url)
            result["text"] = "URL request timed out after 15 seconds. Web search citations will be used for verification."
            if result["keywords"]:
                result["success"] = True
        except httpx.HTTPStatusError as e:
            log.error(f"[Extractor] HTTP {e.response.status_code}: {url}")
            result["keywords"] = self.extract_keywords_from_url(url)
            result["text"] = f"HTTP {e.response.status_code} error fetching URL. Web search citations will be used for verification."
            if result["keywords"]:
                result["success"] = True
        except Exception as e:
            log.error(f"[Extractor] Error: {url}: {e}")
            result["keywords"] = self.extract_keywords_from_url(url)
            result["text"] = f"Extraction anomaly ({str(e)}). Web search citations will be used for verification."
            if result["keywords"]:
                result["success"] = True

        return result

    def _apply_3way_compression(self, cleaned_text: str) -> str:
        """Applies 3-way intelligent evidence compression (First 3k + Middle 4k + Last 3k chars)."""
        max_article_chars = getattr(settings, "MAX_ARTICLE_CHARS", 10000)
        if len(cleaned_text) > max_article_chars:
            first_part = cleaned_text[:3000]
            mid_start = max(0, (len(cleaned_text) // 2) - 2000)
            middle_part = cleaned_text[mid_start:mid_start + 4000]
            last_part = cleaned_text[-3000:]
            return (
                f"{first_part}\n\n"
                f"[... Intro Truncated for Evidence Preservation ({mid_start} chars prior) ...]\n\n"
                f"{middle_part}\n\n"
                f"[... Middle Section Truncated for Conclusion Preservation ...]\n\n"
                f"{last_part}"
            )
        return cleaned_text

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
