import httpx
import feedparser
from datetime import datetime, timezone
from typing import Optional
from ..config.settings import get_settings
from ..utils.logger import log

settings = get_settings()


class NewsService:
    """Fetches news from multiple sources: RSS feeds, GDELT, Google News RSS."""

    def __init__(self):
        self.timeout = settings.RSS_FEED_TIMEOUT
        self.max_sources = settings.MAX_SOURCES_PER_QUERY

        # RSS feeds for major trusted sources
        self.rss_feeds = {
            "reuters": "https://feeds.reuters.com/reuters/topNews",
            "bbc": "http://feeds.bbci.co.uk/news/rss.xml",
            "aljazeera": "https://www.aljazeera.com/xml/rss/all.xml",
            "thehindu": "https://www.thehindu.com/news/feeder/default.rss",
            "ndtv": "https://feeds.feedburner.com/ndtvnews-latest",
            "scroll": "https://scroll.in/feed",
            "thewire": "https://thewire.in/feed",
        }

    async def search_google_news_rss(self, query: str, language: str = "en") -> list[dict]:
        """Search using Google News RSS (free, no API key required)."""
        encoded_query = query.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl={language}&gl=IN&ceid=IN:en"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                feed = feedparser.parse(response.text)

                sources = []
                for entry in feed.entries[:self.max_sources]:
                    published = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                    sources.append({
                        "url": entry.get("link", ""),
                        "title": entry.get("title", ""),
                        "snippet": entry.get("summary", ""),
                        "source_name": entry.get("source", {}).get("title", "Unknown") if hasattr(entry, "source") else "Google News",
                        "published_at": published,
                    })

                return sources

        except httpx.TimeoutException:
            log.warning(f"Google News RSS timeout for query: {query}")
            return []
        except Exception as e:
            log.error(f"Google News RSS error: {e}")
            return []

    async def fetch_source_feed(self, source_key: str) -> list[dict]:
        """Fetch latest articles from a specific RSS feed."""
        feed_url = self.rss_feeds.get(source_key)
        if not feed_url:
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(feed_url)
                response.raise_for_status()
                feed = feedparser.parse(response.text)

                articles = []
                for entry in feed.entries[:10]:
                    published = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                    articles.append({
                        "url": entry.get("link", ""),
                        "title": entry.get("title", ""),
                        "snippet": entry.get("summary", "")[:300],
                        "source_name": feed.feed.get("title", source_key),
                        "published_at": published,
                        "feed_source": source_key,
                    })

                return articles

        except Exception as e:
            log.error(f"RSS feed error for {source_key}: {e}")
            return []

    async def search_gdelt(self, query: str) -> list[dict]:
        """
        Query GDELT API for news articles.
        Free, no API key required.
        """
        params = {
            "mode": "ArticleList",
            "maxrecords": str(self.max_sources),
            "format": "json",
            "query": query,
            "timespan": "7d",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(settings.GDELT_BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                articles = []
                for article in data.get("articles", [])[:self.max_sources]:
                    articles.append({
                        "url": article.get("url", ""),
                        "title": article.get("title", ""),
                        "snippet": article.get("seendate", ""),
                        "source_name": article.get("sourcecountry", "Unknown"),
                        "published_at": None,  # GDELT uses seendate
                        "language": article.get("language", "Unknown"),
                    })

                return articles

        except Exception as e:
            log.error(f"GDELT API error: {e}")
            return []


# Singleton
news_service = NewsService()
