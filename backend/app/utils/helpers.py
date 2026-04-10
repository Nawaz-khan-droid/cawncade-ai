import hashlib
import re
from datetime import datetime, timezone
from typing import Any


def compute_hash(text: str) -> str:
    """Generate SHA-256 hash for deduplication."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def truncate_text(text: str, max_chars: int = 500) -> str:
    """Truncate text to max_chars with ellipsis."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


def is_valid_url(url: str) -> bool:
    """Basic URL validation."""
    pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(pattern.match(url))


def extract_domain(url: str) -> str | None:
    """Extract root domain from URL."""
    match = re.match(r"https?://([^/]+)", url)
    if match:
        domain = match.group(1)
        # Remove www. prefix
        domain = re.sub(r"^www\.", "", domain)
        return domain
    return None


def compute_recency(published_at: datetime | None) -> float:
    """
    Compute recency score (0.0 to 1.0).
    Fresher sources get higher scores.
    """
    if published_at is None:
        return 0.3  # Unknown recency = low-mid

    now = datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    delta_hours = (now - published_at).total_seconds() / 3600

    if delta_hours < 1:
        return 1.0
    elif delta_hours < 6:
        return 0.9
    elif delta_hours < 24:
        return 0.8
    elif delta_hours < 72:
        return 0.65
    elif delta_hours < 168:  # 1 week
        return 0.5
    elif delta_hours < 720:  # 1 month
        return 0.3
    else:
        return 0.1


def normalize_score(score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a score to [min_val, max_val]."""
    return max(min_val, min(max_val, score))


def format_sources_for_prompt(sources: list[dict]) -> str:
    """Format retrieved sources into a structured string for LLM context."""
    if not sources:
        return "No sources retrieved."

    lines = []
    for i, src in enumerate(sources, 1):
        lines.append(f"[Source {i}] {src.get('source_name', 'Unknown')}")
        lines.append(f"  URL: {src.get('url', 'N/A')}")
        lines.append(f"  Title: {src.get('title', 'N/A')}")
        lines.append(f"  Credibility: {src.get('credibility_score', 'N/A')}")
        lines.append(f"  Snippet: {src.get('snippet', 'N/A')}")
        lines.append(f"  Published: {src.get('published_at', 'Unknown')}")
        lines.append("")

    return "\n".join(lines)


def safe_json_serialize(obj: Any) -> Any:
    """Make an object JSON-serializable."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    return obj
