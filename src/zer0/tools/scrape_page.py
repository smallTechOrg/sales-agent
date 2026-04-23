"""scrape_page tool.

Spec: spec/product/02-architecture.md — Tools table
Spec: spec/product/04-capabilities/02-enrichment.md — Sub-step 1: Scrape links
Input:  URL (str)
Output: cleaned page text (str)
"""

from __future__ import annotations

from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup  # type: ignore[import-untyped]

# Realistic browser headers reduce 403 rejections from sites that block
# headless HTTP clients.  These match what a Chrome browser sends.
_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

_HTML_CONTENT_TYPES = ("text/html", "text/plain", "application/xhtml")

# Domains that require auth/JS or actively block HTTP clients.
# Links from these domains are saved and marked 'blocked' — not retried per-run
# but re-attempted when new scrapers are added. LinkedIn is NOT here because
# public company pages are sometimes accessible.
_BLOCKED_DOMAINS: frozenset[str] = frozenset({
    "facebook.com", "www.facebook.com", "m.facebook.com",
    "twitter.com", "www.twitter.com", "x.com", "www.x.com",
    "instagram.com", "www.instagram.com",
    "tiktok.com", "www.tiktok.com",
    "pinterest.com", "www.pinterest.com",
    "snapchat.com", "www.snapchat.com",
    "youtube.com", "www.youtube.com", "youtu.be",
    "reddit.com", "www.reddit.com", "old.reddit.com",
})


def is_blocked_domain(url: str) -> bool:
    """Return True if this URL belongs to a domain we cannot scrape via HTTP."""
    try:
        host = urlparse(url).hostname or ""
        return host in _BLOCKED_DOMAINS
    except Exception:
        return False


def scrape_page(url: str) -> str:
    """Fetch a URL and return cleaned readable text.

    Returns empty string for non-HTML content types (PDFs, binary files, etc.)
    to prevent NUL bytes from crashing PostgreSQL TEXT column writes.
    Raises httpx.HTTPStatusError on 4xx/5xx after following redirects.
    Callers should check is_blocked_domain() before calling this.
    """
    with httpx.Client(headers=_HEADERS, timeout=15.0, follow_redirects=True) as client:
        response = client.get(url)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if not any(content_type.startswith(ct) for ct in _HTML_CONTENT_TYPES):
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    return " ".join(soup.get_text(separator=" ").split()).replace("\x00", "")
