"""
YouTube Service v3.0 — Dual-Stream Architecture.

Stream 1 (API): YouTube Data API v3 via GOOGLE_API_KEY
  → Fetches: title, description, channel, views, duration, publish date, thumbnails
  → Fast, reliable, uses official API quota

Stream 2 (Scraper): youtube-transcript-api via WEBSHARE_PROXY_URL
  → Fetches: full transcript/subtitles for fact-checking
  → No API cost, uses Webshare rotating proxy to avoid IP blocks

Fallback: If API quota is exceeded (403/403), scraper attempts metadata extraction.
All Google services share the single GOOGLE_API_KEY (5-in-1).
"""

import re
import asyncio
import httpx
from app.config.settings import get_settings
from app.core.cache import cache
from app.core.resilience import circuit_youtube
from app.utils.logger import log

settings = get_settings()

# ── Video ID Extraction ──

def _get_video_id(url: str) -> str | None:
    """Extract 11-char YouTube video ID from various URL formats."""
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com/watch\?.*[?&]v=([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def is_youtube_url(url: str) -> bool:
    """Check if a URL is a valid YouTube video URL."""
    return bool(_get_video_id(url))


# ═══════════════════════════════════════════════════════════════
# STREAM 1: YouTube Data API v3 (Official — uses GOOGLE_API_KEY)
# ═══════════════════════════════════════════════════════════════

async def fetch_video_metadata_api(video_id: str) -> dict:
    """
    Fetch video metadata via YouTube Data API v3.
    Uses the SAME GOOGLE_API_KEY as CSE, Fact Check, Safe Browsing, and GCS.
    Returns: title, description, channel, viewCount, duration, publishedAt, thumbnails.
    """
    if not settings.GOOGLE_API_KEY:
        return {"error": "GOOGLE_API_KEY not configured", "source": "api"}

    cache_key = f"yt_meta_api:{video_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return {**cached, "cached": True}

    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,contentDetails,statistics",
        "id": video_id,
        "key": settings.GOOGLE_API_KEY,
    }

    async def _call():
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 403:
                return {"error": "quota_exceeded", "status_code": 403, "source": "api"}
            if resp.status_code == 429:
                return {"error": "rate_limited", "status_code": 429, "source": "api"}
            resp.raise_for_status()
            return resp.json()

    result = await circuit_youtube.call(_call)
    if result is None:
        return {"error": "Service unavailable", "source": "api"}

    if isinstance(result, dict) and result.get("error"):
        return {"error": result.get("message", "API error"), "source": "api"}

    items = result.get("items", [])
    if not items:
        return {"error": "Video not found or private", "source": "api"}

    video = items[0]
    snippet = video.get("snippet", {})
    content = video.get("contentDetails", {})
    stats = video.get("statistics", {})

    # Parse ISO 8601 duration (PT1H30M45S -> seconds)
    duration_str = content.get("duration", "PT0S")
    duration_seconds = _parse_iso_duration(duration_str)

    output = {
        "video_id": video_id,
        "source": "youtube_api_v3",
        "title": snippet.get("title", ""),
        "description": snippet.get("description", "")[:2000],
        "channel": snippet.get("channelTitle", ""),
        "channel_id": snippet.get("channelId", ""),
        "published_at": snippet.get("publishedAt", ""),
        "view_count": int(stats.get("viewCount", 0)),
        "like_count": int(stats.get("likeCount", 0)),
        "comment_count": int(stats.get("commentCount", 0)),
        "duration_seconds": duration_seconds,
        "duration_iso": duration_str,
        "thumbnails": snippet.get("thumbnails", {}),
        "tags": snippet.get("tags", []),
        "category_id": snippet.get("categoryId", ""),
        "default_language": snippet.get("defaultAudioLanguage", ""),
        "success": True,
    }

    cache.set(cache_key, output, ttl=settings.YOUTUBE_CACHE_TTL)
    log.info(f"[YouTube API] Metadata fetched: {snippet.get('title', 'N/A')[:60]} ({duration_seconds}s)")
    return output


def _parse_iso_duration(iso: str) -> int:
    """Convert YouTube ISO 8601 duration (PT1H30M45S) to seconds."""
    if not iso:
        return 0
    total = 0
    pattern = r"(\d+)([HMS])"
    for match in re.finditer(pattern, iso):
        value = int(match.group(1))
        unit = match.group(2)
        if unit == "H":
            total += value * 3600
        elif unit == "M":
            total += value * 60
        elif unit == "S":
            total += value
    return total


# ═══════════════════════════════════════════════════════════════
# STREAM 2: Transcript Scraper (youtube-transcript-api + Webshare)
# ═══════════════════════════════════════════════════════════════

def _get_proxy_config():
    """Build Webshare proxy config from HF Secrets (URL + USER + PASS)."""
    proxy_url = settings.WEBSHARE_PROXY_URL
    proxy_user = settings.WEBSHARE_PROXY_USER
    proxy_pass = settings.WEBSHARE_PROXY_PASS

    if not proxy_url and not proxy_user:
        return None

    try:
        from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig

        # If Webshare credentials are available, use WebshareProxyConfig
        if proxy_user and proxy_pass:
            return WebshareProxyConfig(proxy_username=proxy_user, proxy_password=proxy_pass)

        # Fallback: generic proxy URL (auto-parses user:pass from URL)
        if proxy_url:
            return GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)

        return None
    except Exception as e:
        log.warning(f"[YouTube Scraper] Failed to parse proxy: {e}")
        return None


async def fetch_transcript_scraper(video_id: str, languages: list = None) -> dict:
    """
    Fetch video transcript using youtube-transcript-api with Webshare proxy.
    This is the deep analysis stream — extracts actual subtitles for fact-checking.
    """
    if languages is None:
        languages = ["en", "hi"]

    cache_key = f"yt_transcript:{video_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return {**cached, "cached": True}

    try:
        loop = asyncio.get_event_loop()

        def _fetch():
            proxy_config = _get_proxy_config()
            if proxy_config:
                api = YouTubeTranscriptApi(proxy_config=proxy_config)
            else:
                api = YouTubeTranscriptApi()

            try:
                transcript_list = api.list(video_id)
                transcript = transcript_list.find_transcript(languages)
            except Exception:
                transcript = api.fetch(video_id, languages=languages)

            from youtube_transcript_api.formatters import TextFormatter
            return TextFormatter().format_transcript(transcript), transcript

        result = await circuit_youtube.call(lambda: loop.run_in_executor(None, _fetch))

        if result is None:
            return {"video_id": video_id, "transcript": "", "error": "Service unavailable",
                    "source": "scraper", "success": False}

        transcript_text, raw_transcript = result

        # Calculate duration from transcript snippets
        duration = 0.0
        try:
            snippets = list(raw_transcript)
            if snippets:
                duration = snippets[-1].start + (getattr(snippets[-1], 'duration', 0) or 0)
        except Exception:
            pass

        output = {
            "video_id": video_id,
            "transcript": transcript_text,
            "language": getattr(raw_transcript, "language_code", "en"),
            "duration": duration,
            "source": "scraper",
            "success": True,
        }

        cache.set(cache_key, output, ttl=settings.YOUTUBE_CACHE_TTL)
        log.info(f"[YouTube Scraper] Transcript extracted: {video_id} ({duration:.0f}s)")
        return output

    except Exception as e:
        error_msg = str(e)
        if "TranscriptNotFound" in error_msg or "Could not retrieve" in error_msg:
            error_msg = "No transcript available for this video"
        elif "RequestBlocked" in error_msg or "IpBlocked" in error_msg:
            error_msg = "YouTube blocked the request. Check Webshare proxy credentials."
        log.error(f"[YouTube Scraper] Failed for {video_id}: {error_msg}")
        return {"video_id": video_id, "transcript": "", "error": error_msg,
                "source": "scraper", "success": False}


# ═══════════════════════════════════════════════════════════════
# UNIFIED DUAL-STREAM ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

async def analyze_youtube(video_url: str, languages: list = None) -> dict:
    """
    Dual-Stream YouTube Analysis:
    1. API Stream: Fetch metadata (title, description, views, channel) via YouTube Data API v3
    2. Scraper Stream: Fetch transcript via youtube-transcript-api + Webshare proxy
    3. Merge both into unified result for fact-checking pipeline

    Fallback: If API quota exceeded, scraper-only mode with limited metadata.
    """
    video_id = _get_video_id(video_url)
    if not video_id:
        return {"video_id": None, "error": "Invalid YouTube URL", "success": False,
                "source": "none", "url": video_url}

    log.info(f"[YouTube Dual-Stream] Analyzing video: {video_id}")

    # Run both streams in parallel for speed
    api_task = fetch_video_metadata_api(video_id)
    scraper_task = fetch_transcript_scraper(video_id, languages)

    api_result, scraper_result = await asyncio.gather(
        api_task, scraper_task, return_exceptions=True
    )

    # Handle exceptions
    if isinstance(api_result, Exception):
        log.error(f"[YouTube API] Exception: {api_result}")
        api_result = {"error": str(api_result), "source": "api", "success": False}
    if isinstance(scraper_result, Exception):
        log.error(f"[YouTube Scraper] Exception: {scraper_result}")
        scraper_result = {"error": str(scraper_result), "source": "scraper", "success": False}

    # Merge results
    merged = {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "success": False,
        "api_stream": api_result.get("source", "failed"),
        "scraper_stream": scraper_result.get("source", "failed"),
    }

    # Metadata from API (Stream 1)
    if api_result.get("success"):
        merged["title"] = api_result.get("title", "")
        merged["description"] = api_result.get("description", "")
        merged["channel"] = api_result.get("channel", "")
        merged["view_count"] = api_result.get("view_count", 0)
        merged["published_at"] = api_result.get("published_at", "")
        merged["duration"] = api_result.get("duration_seconds", 0)
        merged["thumbnails"] = api_result.get("thumbnails", {})
        merged["tags"] = api_result.get("tags", [])
        merged["api_metadata_complete"] = True

        # If API gave us a description, use it as fallback query
        if not scraper_result.get("success") and api_result.get("description"):
            merged["description_fallback"] = True
            log.info(f"[YouTube Dual-Stream] API succeeded, Scraper failed — using description as fallback")

    # Transcript from Scraper (Stream 2)
    if scraper_result.get("success"):
        merged["transcript"] = scraper_result.get("transcript", "")
        merged["transcript_language"] = scraper_result.get("language", "en")
        if not merged.get("duration"):
            merged["duration"] = scraper_result.get("duration", 0)

    # Quota exceeded fallback: Scraper-only mode
    if api_result.get("error") == "quota_exceeded":
        merged["quota_exceeded"] = True
        log.warning("[YouTube Dual-Stream] API quota exceeded — running in scraper-only mode")
        if scraper_result.get("success"):
            merged["success"] = True
            # Try to extract title from transcript first line
            if scraper_result.get("transcript"):
                first_lines = scraper_result["transcript"][:200].strip()
                merged["title_fallback"] = first_lines[:100]

    # Both streams failed
    if not api_result.get("success") and not scraper_result.get("success"):
        merged["success"] = False
        merged["error"] = f"API: {api_result.get('error', 'failed')}. Scraper: {scraper_result.get('error', 'failed')}"
        return merged

    # At least one stream succeeded
    if not merged.get("success"):
        merged["success"] = True

    log.info(
        f"[YouTube Dual-Stream] Result: API={api_result.get('success', False)}, "
        f"Scraper={scraper_result.get('success', False)}, "
        f"Title='{merged.get('title', 'N/A')[:50]}'"
    )
    return merged


# Legacy compatibility — called by orchestrator
async def extract_transcript(video_url: str, languages: list = None) -> dict:
    """
    Legacy function for backward compatibility.
    Internally calls the full Dual-Stream analyzer and returns transcript-focused result.
    """
    result = await analyze_youtube(video_url, languages)
    return {
        "video_id": result.get("video_id"),
        "transcript": result.get("transcript", ""),
        "title": result.get("title", ""),
        "description": result.get("description", ""),
        "channel": result.get("channel", ""),
        "duration": result.get("duration", 0),
        "language": result.get("transcript_language", "en"),
        "success": result.get("success", False),
        "error": result.get("error"),
        "source": "dual_stream",
        "api_stream": result.get("api_stream"),
        "scraper_stream": result.get("scraper_stream"),
    }


# Import at module level (lazy import in _get_proxy_config to avoid errors if not installed)
from youtube_transcript_api import YouTubeTranscriptApi
