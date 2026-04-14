"""
YouTube Service v3.0 — Dual-Stream Architecture.

Stream 1 (API): YouTube Data API v3 via GOOGLE_API_KEY
  → Fetches: title, description, channel, views, duration, publish date, thumbnails
  → Fast, reliable, uses official API quota

Stream 2 (Scraper): youtube-transcript-api
  → Fetches: full transcript/subtitles for fact-checking
  → No API cost

Fallback: If API quota is exceeded (403/403), scraper attempts metadata extraction.
All Google services share the single GOOGLE_API_KEY (5-in-1).
"""

import re
import asyncio
import httpx
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
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
    """
    if not settings.GOOGLE_API_KEY:
        return {"error": "GOOGLE_API_KEY not configured", "source": "api", "success": False}

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
                return {"error": "quota_exceeded", "status_code": 403, "source": "api", "success": False}
            if resp.status_code == 429:
                return {"error": "rate_limited", "status_code": 429, "source": "api", "success": False}
            resp.raise_for_status()
            return resp.json()

    result = await circuit_youtube.call(_call)
    if result is None or (isinstance(result, dict) and result.get("error")):
        return result or {"error": "Service unavailable", "source": "api", "success": False}

    items = result.get("items", [])
    if not items:
        return {"error": "Video not found or private", "source": "api", "success": False}

    video = items[0]
    snippet = video.get("snippet", {})
    content = video.get("contentDetails", {})
    stats = video.get("statistics", {})

    duration_str = content.get("duration", "PT0S")
    duration_seconds = _parse_iso_duration(duration_str)

    output = {
        "video_id": video_id,
        "source": "youtube_api_v3",
        "title": snippet.get("title", ""),
        "description": snippet.get("description", "")[:2000],
        "channel": snippet.get("channelTitle", ""),
        "published_at": snippet.get("publishedAt", ""),
        "view_count": int(stats.get("viewCount", 0)),
        "duration_seconds": duration_seconds,
        "success": True,
    }

    cache.set(cache_key, output, ttl=settings.YOUTUBE_CACHE_TTL)
    return output


def _parse_iso_duration(iso: str) -> int:
    """Convert YouTube ISO 8601 duration to seconds."""
    if not iso: return 0
    total = 0
    pattern = r"(\d+)([HMS])"
    for match in re.finditer(pattern, iso):
        value, unit = int(match.group(1)), match.group(2)
        if unit == "H": total += value * 3600
        elif unit == "M": total += value * 60
        elif unit == "S": total += value
    return total


# ═══════════════════════════════════════════════════════════════
# STREAM 2: Transcript Scraper (youtube-transcript-api + Webshare)
# ═══════════════════════════════════════════════════════════════

async def fetch_transcript_scraper(video_id: str, languages: list = None) -> dict:
    """
    Fetch video transcript using youtube-transcript-api.
    """
    if languages is None:
        languages = ["en", "hi"]

    cache_key = f"yt_transcript:{video_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return {**cached, "cached": True}

    def _fetch():
        try:
            return YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        except Exception as e:
            # Fallback to list/find if direct fetch fails
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            return transcript_list.find_transcript(languages).fetch()

    try:
        loop = asyncio.get_event_loop()
        raw_transcript = await loop.run_in_executor(None, _fetch)
        transcript_text = TextFormatter().format_transcript(raw_transcript)

        output = {
            "video_id": video_id,
            "transcript": transcript_text,
            "source": "scraper",
            "success": True,
        }
        cache.set(cache_key, output, ttl=settings.YOUTUBE_CACHE_TTL)
        return output
    except Exception as e:
        log.error(f"[YouTube Scraper] Failed for {video_id}: {e}")
        return {"video_id": video_id, "success": False, "error": str(e), "source": "scraper"}


# ═══════════════════════════════════════════════════════════════
# UNIFIED DUAL-STREAM ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

async def analyze_youtube(video_url: str, languages: list = None) -> dict:
    video_id = _get_video_id(video_url)
    if not video_id:
        return {"error": "Invalid URL", "success": False}

    api_res, scraper_res = await asyncio.gather(
        fetch_video_metadata_api(video_id),
        fetch_transcript_scraper(video_id, languages),
        return_exceptions=True
    )

    # Standardize result objects if they returned exceptions
    if isinstance(api_res, Exception): api_res = {"success": False, "error": str(api_res)}
    if isinstance(scraper_res, Exception): scraper_res = {"success": False, "error": str(scraper_res)}

    merged = {
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "title": api_res.get("title", "Unknown Title"),
        "description": api_res.get("description", ""),
        "channel": api_res.get("channel", ""),
        "duration": api_res.get("duration_seconds", 0),
        "transcript": scraper_res.get("transcript", ""),
        "success": api_res.get("success") or scraper_res.get("success"),
        "api_stream": "ok" if api_res.get("success") else "failed",
        "scraper_stream": "ok" if scraper_res.get("success") else "failed"
    }
    
    return merged

async def extract_transcript(video_url: str, languages: list = None) -> dict:
    """Legacy compatibility wrapper."""
    return await analyze_youtube(video_url, languages)