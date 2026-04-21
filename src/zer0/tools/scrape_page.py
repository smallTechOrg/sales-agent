"""scrape_page tool.

Spec: spec/product/02-architecture.md — Tools table
Input:  URL (str)
Output: cleaned page text (str)
"""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup  # type: ignore[import-untyped]


def scrape_page(url: str) -> str:
    """Fetch a URL and return cleaned readable text.

    Strips navigation, scripts, styles. Returns best-effort plain text.
    """
    response = httpx.get(url, timeout=15.0, follow_redirects=True)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    return " ".join(soup.get_text(separator=" ").split())
