"""
CAWNCADE AI v3.0 — Trusted Source Domains.
50 curated domains for the Google CSE "High-Trust Filter" (Walled Garden).
Organized by trust tier with scoring multipliers.

This list is also used in site:domain.com queries for Google Custom Search (Tier 2)
and as include_domains for Tavily (Tier 3).
"""

# ── TIER 1: DEDICATED FACT-CHECKERS (Highest Trust) — Score multiplier: 1.0 ──
FACT_CHECKERS = [
    "altnews.in",
    "boomlive.in",
    "factchecker.in",
    "factly.in",
    "newschecker.in",
    "thequint.com",
    "politifact.com",
    "snopes.com",
]

# ── TIER 2: PRIMARY NEWS AGENCIES & WIRES — Score multiplier: 0.85 ──
WIRE_SERVICES = [
    "reuters.com",
    "apnews.com",
    "msn.com",
    "ptinews.com",
    "aninews.in",
    "bbc.com",
]

# ── TIER 3: TRUSTED EDITORIAL NEWS — Score multiplier: 0.7 ──
EDITORIAL_NEWS = [
    "thehindu.com",
    "indianexpress.com",
    "hindustantimes.com",
    "deccanherald.com",
    "tribuneindia.com",
    "business-standard.com",
    "livemint.com",
    "ndtv.com",
    "scroll.in",
    "thewire.in",
    "thenewsminute.com",
    "newslaundry.com",
    "caravanmagazine.in",
    "theprint.in",
    "article-14.com",
    "theguardian.com",
    "aljazeera.com",
    "dw.com",
    "economist.com",
    "wsj.com",
    "ft.com",
    "euronews.com",
    "scmp.com",
    "telegraphindia.com",
]

# ── TIER 4: REFERENCE, SPECIALIZED & DISCUSSION — Score multiplier: 0.6 ──
SPECIALIZED_REFERENCE = [
    "prsindia.org",
    "indiaspend.com",
    "wikipedia.org",
    "encyclopedia.com",
    "britannica.com",
    "forbes.com",
    "news.un.org",
    "hrw.org",
    "unep.org",
    "pib.gov.in",
]

# ── TIER 5: DISCUSSION & AGGREGATION — Score multiplier: 0.45 ──
DISCUSSION_PLATFORMS = [
    "reddit.com",
    "x.com",
    "news.google.com",
]

# ── WILDCARD DOMAINS (subdomain patterns) ──
WILDCARD_DOMAINS = [
    "*.muslimmirror.com",
]

# ── COMPLETE LIST (all 50 domains) ──
ALL_TRUSTED_DOMAINS = (
    FACT_CHECKERS + WIRE_SERVICES + EDITORIAL_NEWS
    + SPECIALIZED_REFERENCE + DISCUSSION_PLATFORMS
)

# ── DOMAIN TRUST MAP (for scoring) ──
DOMAIN_TRUST_MAP = {}

for domain in FACT_CHECKERS:
    DOMAIN_TRUST_MAP[domain] = {"tier": 1, "label": "fact_checker", "multiplier": 1.0}
for domain in WIRE_SERVICES:
    DOMAIN_TRUST_MAP[domain] = {"tier": 2, "label": "wire_service", "multiplier": 0.85}
for domain in EDITORIAL_NEWS:
    DOMAIN_TRUST_MAP[domain] = {"tier": 3, "label": "editorial", "multiplier": 0.7}
for domain in SPECIALIZED_REFERENCE:
    DOMAIN_TRUST_MAP[domain] = {"tier": 4, "label": "specialized", "multiplier": 0.6}
for domain in DISCUSSION_PLATFORMS:
    DOMAIN_TRUST_MAP[domain] = {"tier": 5, "label": "discussion", "multiplier": 0.45}


def get_trust_info(domain: str) -> dict:
    """Get trust tier and scoring multiplier for a domain."""
    if not domain:
        return {"tier": 0, "label": "unknown", "multiplier": 0.4}
    clean = domain.lower().replace("www.", "").strip()
    if "muslimmirror.com" in clean:
        return {"tier": 4, "label": "specialized", "multiplier": 0.6}

    # Direct match first
    if clean in DOMAIN_TRUST_MAP:
        return DOMAIN_TRUST_MAP[clean]

    # Handle subdomains & multi-part TLDs (e.g. news.bbc.co.uk -> bbc.co.uk or edition.cnn.com -> cnn.com)
    parts = clean.split(".")
    if len(parts) >= 3:
        # Check last 3 parts (e.g. bbc.co.uk)
        last3 = ".".join(parts[-3:])
        if last3 in DOMAIN_TRUST_MAP:
            return DOMAIN_TRUST_MAP[last3]
        # Check last 2 parts (e.g. cnn.com)
        last2 = ".".join(parts[-2:])
        if last2 in DOMAIN_TRUST_MAP:
            return DOMAIN_TRUST_MAP[last2]

    return {"tier": 0, "label": "unknown", "multiplier": 0.4}


def get_domains_by_tier(tier: int) -> list:
    """Get all domains in a specific trust tier."""
    return [d for d, info in DOMAIN_TRUST_MAP.items() if info["tier"] == tier]


def get_google_site_filter(max_domains: int = 50) -> str:
    """
    Build a Google CSE site: filter string using the full 50-domain list.
    This restricts Google Custom Search to ONLY the trusted domains (Walled Garden).
    Uses OR syntax: site:altnews.in OR site:boomlive.in OR ...
    """
    # Priority order: fact-checkers first, then wires, then editorial, etc.
    prioritized = (
        FACT_CHECKERS + WIRE_SERVICES + EDITORIAL_NEWS[:10]
        + SPECIALIZED_REFERENCE[:5] + DISCUSSION_PLATFORMS
    )
    domains = [d for d in prioritized if not d.startswith("*")]
    # Add wildcard domains as base patterns
    for wd in WILDCARD_DOMAINS:
        base = wd.replace("*.", "")
        if base not in domains:
            domains.append(base)

    selected = domains[:max_domains]
    return " OR ".join([f"site:{d}" for d in selected])
