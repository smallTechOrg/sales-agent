# Unit tests for scrape_page tool
# Spec: spec/product/04-capabilities/02-enrichment.md — Sub-step 1: Scrape links
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from zer0.tools.scrape_page import scrape_page


def _mock_response(
    *,
    text: str = "<html><body><p>Hello world</p></body></html>",
    content_type: str = "text/html; charset=utf-8",
    status_code: int = 200,
) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    resp.headers = {"content-type": content_type}
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    return resp


def _patch_client(response: MagicMock):
    """Return a context-manager patch for httpx.Client that yields the mock response."""
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = response
    return patch("zer0.tools.scrape_page.httpx.Client", return_value=mock_client)


class TestScrapePageHTMLContent:
    def test_returns_cleaned_text_for_html_response(self) -> None:
        resp = _mock_response(text="<html><body><p>Hello world</p></body></html>")
        with _patch_client(resp):
            result = scrape_page("https://example.com")
        assert "Hello world" in result

    def test_strips_script_and_style_tags(self) -> None:
        html = "<html><body><script>alert(1)</script><p>Visible</p><style>a{}</style></body></html>"
        resp = _mock_response(text=html)
        with _patch_client(resp):
            result = scrape_page("https://example.com")
        assert "Visible" in result
        assert "alert" not in result

    def test_xhtml_content_type_is_parsed(self) -> None:
        resp = _mock_response(
            text="<html><body><p>XHTML page</p></body></html>",
            content_type="application/xhtml+xml",
        )
        with _patch_client(resp):
            result = scrape_page("https://example.com")
        assert "XHTML page" in result

    def test_text_plain_content_type_is_parsed(self) -> None:
        resp = _mock_response(
            text="plain text content",
            content_type="text/plain; charset=utf-8",
        )
        with _patch_client(resp):
            result = scrape_page("https://example.com")
        assert "plain text content" in result


class TestScrapePageBinaryContent:
    def test_pdf_content_type_returns_empty_string(self) -> None:
        resp = _mock_response(
            text="\x00\x01binary garbage",
            content_type="application/pdf",
        )
        with _patch_client(resp):
            result = scrape_page("https://example.com/file.pdf")
        assert result == ""

    def test_octet_stream_content_type_returns_empty_string(self) -> None:
        resp = _mock_response(
            text="\x00\xff binary",
            content_type="application/octet-stream",
        )
        with _patch_client(resp):
            result = scrape_page("https://example.com/download")
        assert result == ""

    def test_missing_content_type_returns_empty_string(self) -> None:
        resp = _mock_response(text="data", content_type="")
        with _patch_client(resp):
            result = scrape_page("https://example.com/unknown")
        assert result == ""


class TestScrapePageNulBytes:
    def test_nul_bytes_stripped_from_html_response(self) -> None:
        """Even if HTML somehow contains NUL bytes, they must be stripped before return."""
        html = "<html><body><p>Clean\x00text</p></body></html>"
        resp = _mock_response(text=html, content_type="text/html")
        with _patch_client(resp):
            result = scrape_page("https://example.com")
        assert "\x00" not in result
        assert "Clean" in result
        assert "text" in result
