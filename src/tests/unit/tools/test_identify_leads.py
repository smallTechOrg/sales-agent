# Unit tests for identify_leads tool
# Spec: spec/product/04-capabilities/02-enrichment.md — Sub-step 2: Identify leads
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from zer0.domain import ICP, Link
from zer0.domain.config import CompanySizeRange, ResolvedConfig
from zer0.domain.link import LinkSource
from zer0.tools.identify_leads import identify_leads


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_icp(**kwargs) -> ICP:
    defaults = dict(
        target_industries=["SaaS", "Fintech"],
        target_roles=["CTO", "VP Engineering"],
        company_size_range=CompanySizeRange(min=50, max=500),
        geography=["US"],
        keywords=["cloud"],
        negative_keywords=["casino"],
    )
    defaults.update(kwargs)
    return ICP(**defaults)


def _make_link(page_text: str | None = "some text") -> Link:
    return Link(
        id="link-1",
        campaign_id="camp-1",
        tenant_id="tenant-1",
        url="https://example.com",
        source=LinkSource.web,
        page_text=page_text,
    )


def _make_llm(response: str) -> MagicMock:
    llm = MagicMock()
    llm.load_prompt.return_value = "system prompt"
    llm.complete.return_value = response
    return llm


def _make_config() -> ResolvedConfig:
    return MagicMock(spec=ResolvedConfig)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestIdentifyLeadsICPFields:
    def test_company_size_range_used_in_prompt(self) -> None:
        """ICP company_size_range.min/max must appear in the user message, not flat attrs."""
        icp = _make_icp()
        llm = _make_llm("[]")
        config = _make_config()

        identify_leads(link=_make_link(), icp=icp, llm=llm, config=config)

        call_kwargs = llm.complete.call_args
        user_msg = call_kwargs.kwargs.get("user") or call_kwargs.args[1]
        assert "50" in user_msg
        assert "500" in user_msg

    def test_icp_industries_in_prompt(self) -> None:
        icp = _make_icp()
        llm = _make_llm("[]")
        config = _make_config()

        identify_leads(link=_make_link(), icp=icp, llm=llm, config=config)

        call_kwargs = llm.complete.call_args
        user_msg = call_kwargs.kwargs.get("user") or call_kwargs.args[1]
        assert "SaaS" in user_msg
        assert "Fintech" in user_msg


class TestIdentifyLeadsNoPageText:
    def test_no_page_text_returns_empty_list(self) -> None:
        llm = MagicMock()
        result = identify_leads(
            link=_make_link(page_text=None),
            icp=_make_icp(),
            llm=llm,
            config=_make_config(),
        )
        assert result == []
        llm.complete.assert_not_called()

    def test_empty_page_text_returns_empty_list(self) -> None:
        llm = MagicMock()
        result = identify_leads(
            link=_make_link(page_text=""),
            icp=_make_icp(),
            llm=llm,
            config=_make_config(),
        )
        assert result == []
        llm.complete.assert_not_called()


class TestIdentifyLeadsValidResponse:
    def test_single_company_entry_returns_one_lead(self) -> None:
        payload = json.dumps([
            {"company_name": "Acme Corp", "domain": "acme.com", "industry": "SaaS",
             "headcount_range": "50-200", "business_type": "B2B"}
        ])
        result = identify_leads(
            link=_make_link(),
            icp=_make_icp(),
            llm=_make_llm(payload),
            config=_make_config(),
        )
        assert len(result) == 1
        lead = result[0]
        assert lead.company_name == "Acme Corp"
        assert lead.domain == "acme.com"
        assert lead.industry == "SaaS"
        assert lead.headcount_range == "50-200"
        assert lead.business_type == "B2B"
        assert lead.tenant_id == "tenant-1"
        assert lead.campaign_id == "camp-1"
        assert lead.link_id == "link-1"

    def test_multiple_companies_returns_multiple_leads(self) -> None:
        payload = json.dumps([
            {"company_name": "Alpha", "domain": "alpha.io", "industry": "Fintech",
             "headcount_range": None, "business_type": None},
            {"company_name": "Beta", "domain": "beta.io", "industry": "SaaS",
             "headcount_range": "10-50", "business_type": "B2B"},
        ])
        result = identify_leads(
            link=_make_link(),
            icp=_make_icp(),
            llm=_make_llm(payload),
            config=_make_config(),
        )
        assert len(result) == 2
        assert {r.company_name for r in result} == {"Alpha", "Beta"}

    def test_json_wrapped_in_markdown_fences_is_parsed(self) -> None:
        payload = '```json\n[{"company_name": "Fence Corp", "domain": null, "industry": null, "headcount_range": null, "business_type": null}]\n```'
        result = identify_leads(
            link=_make_link(),
            icp=_make_icp(),
            llm=_make_llm(payload),
            config=_make_config(),
        )
        assert len(result) == 1
        assert result[0].company_name == "Fence Corp"

    def test_leads_have_unique_ids(self) -> None:
        payload = json.dumps([
            {"company_name": "A", "domain": None, "industry": None, "headcount_range": None, "business_type": None},
            {"company_name": "B", "domain": None, "industry": None, "headcount_range": None, "business_type": None},
        ])
        result = identify_leads(
            link=_make_link(),
            icp=_make_icp(),
            llm=_make_llm(payload),
            config=_make_config(),
        )
        ids = [r.id for r in result]
        assert len(ids) == len(set(ids))


class TestIdentifyLeadsMalformedResponse:
    def test_malformed_json_returns_empty_list(self) -> None:
        result = identify_leads(
            link=_make_link(),
            icp=_make_icp(),
            llm=_make_llm("not json at all"),
            config=_make_config(),
        )
        assert result == []

    def test_json_object_not_array_returns_empty_list(self) -> None:
        result = identify_leads(
            link=_make_link(),
            icp=_make_icp(),
            llm=_make_llm('{"company_name": "Oops"}'),
            config=_make_config(),
        )
        assert result == []

    def test_empty_array_returns_empty_list(self) -> None:
        result = identify_leads(
            link=_make_link(),
            icp=_make_icp(),
            llm=_make_llm("[]"),
            config=_make_config(),
        )
        assert result == []


class TestIdentifyLeadsEntryFiltering:
    def test_entry_missing_company_name_is_skipped(self) -> None:
        payload = json.dumps([
            {"domain": "ghost.com", "industry": "SaaS", "headcount_range": None, "business_type": None},
            {"company_name": "Visible Co", "domain": "visible.com", "industry": "SaaS",
             "headcount_range": None, "business_type": None},
        ])
        result = identify_leads(
            link=_make_link(),
            icp=_make_icp(),
            llm=_make_llm(payload),
            config=_make_config(),
        )
        assert len(result) == 1
        assert result[0].company_name == "Visible Co"

    def test_entry_with_null_company_name_is_skipped(self) -> None:
        payload = json.dumps([
            {"company_name": None, "domain": "null-co.com", "industry": None,
             "headcount_range": None, "business_type": None},
        ])
        result = identify_leads(
            link=_make_link(),
            icp=_make_icp(),
            llm=_make_llm(payload),
            config=_make_config(),
        )
        assert result == []
