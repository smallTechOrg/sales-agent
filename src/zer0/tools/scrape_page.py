"""scrape_page tool.

Spec: spec/product/02-architecture.md — Tools table
Spec: spec/product/04-capabilities/02-enrichment.md — Sub-step 1: Scrape links
Input:  URL (str)
Output: cleaned page text (str)
"""

from __future__ import annotations

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


def scrape_page(url: str) -> str:
    """Fetch a URL and return cleaned readable text.

    Strips navigation, scripts, styles. Returns best-effort plain text.
    Raises httpx.HTTPStatusError on 4xx/5xx after following redirects.
    """
    with httpx.Client(headers=_HEADERS, timeout=15.0, follow_redirects=True) as client:
        response = client.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    return " ".join(soup.get_text(separator=" ").split())
