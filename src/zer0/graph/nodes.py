"""Graph nodes — one function per node.

Spec: spec/product/10-agent-graph.md — Nodes

Each node accepts AgentState and returns a partial dict merged back into state.
DB writes (stage updates, EventRow inserts, MessageRow inserts) are committed
per-node inside create_db_session() so every action is immediately visible in
the audit trail and UI even if a later node fails.
"""

from __future__ import annotations

import structlog
from datetime import datetime, timezone

from zer0.config.resolver import ConfigResolver
from zer0.db.models import PersonRow, CompanyRow, LeadRow, LinkLeadsRow, LinkRow, MessageRow
from zer0.db.session import create_db_session
from zer0.domain import Person, Company, Lead, Link
from zer0.domain.config import ApprovalMode, Channel
from zer0.domain.lead import LeadStage
from zer0.domain.link import LinkSource as LinkSourceModel
from zer0.domain.outreach import SentMessage
from zer0.graph.state import AgentState
from zer0.llm.client import LLMClient
from zer0.observability.events import post_slack_event, write_event
from zer0.tools import (
    check_replies,
    detect_language,
    directory_search,
    draft_outreach,
    duckduckgo_search,
    enrich_lead,
    find_all_people,
    identify_leads,
    linkedin_search,
    qualify_lead,
    scrape_page,
    send_email,
    send_whatsapp,
    web_search,
)

log = structlog.get_logger(__name__)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _new_id() -> str:
    import uuid
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# resolve_config
# ---------------------------------------------------------------------------

def node_resolve_config(state: AgentState) -> dict:
    """Resolve campaign config from DB. Aborts run on error."""
    try:
        with create_db_session() as session:
            config = ConfigResolver(session).resolve(
                campaign_id=state["campaign_id"],
                tenant_id=state["tenant_id"],
            )
        return {"config": config}
    except Exception as exc:
        log.error("resolve_config.failed", error=str(exc))
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# discover  →  writes LinkRow rows
# ---------------------------------------------------------------------------

def node_discover(state: AgentState) -> dict:
    """Run discovery tools and persist raw Link rows (URLs only — no scraping yet).

    Deduplication is tenant-scoped: a URL already seen for this tenant (in any
    previous campaign) is not re-inserted. The link_leads junction records the
    association between the existing/new link and the current campaign run.
    """
    if state.get("error"):
        return {}

    config = state["config"]
    disc = config.discovery_config
    icp = config.icp
    campaign_id = state["campaign_id"]
    tenant_id = state["tenant_id"]

    # Seed seen_urls from in-memory state links
    seen_urls: set[str] = {lnk.url for lnk in state.get("links", [])}
    # Extend with tenant-wide DB URLs (not just this campaign)
    existing_url_to_id: dict[str, str] = {}
    try:
        with create_db_session() as db_check:
            rows = (
                db_check.query(LinkRow.url, LinkRow.id)
                .filter(LinkRow.tenant_id == tenant_id)
                .all()
            )
            for url, lid in rows:
                existing_url_to_id[url] = lid
                seen_urls.add(url)
    except Exception as exc:
        log.warning("discover.db_dedup_failed", error=str(exc))

    raw_links: list[Link] = []
    reused_links: list[Link] = []  # existing links re-used by this campaign
    settings = None

    base_kwargs: dict = {
        "discovery_config": disc,
        "icp": icp,
        "tenant_id": tenant_id,
        "campaign_id": campaign_id,
    }

    non_web_source_map = {
        "linkedin": (linkedin_search, LinkSourceModel.linkedin),
        "directory": (directory_search, LinkSourceModel.directory),
    }

    for source_name in [s.value for s in disc.sources]:
        if source_name == "web":
            if settings is None:
                from zer0.config.settings import get_settings
                settings = get_settings()

            web_adapters = [("duckduckgo", duckduckgo_search)]
            if settings.tavily_api_key:
                web_adapters.append(("tavily", web_search))

            for adapter_name, adapter_fn in web_adapters:
                try:
                    kwargs = dict(base_kwargs)
                    if adapter_fn is web_search:
                        kwargs["tavily_api_key"] = settings.tavily_api_key
                    results = adapter_fn(**kwargs)
                    log.info("discover.web_adapter_ok", adapter=adapter_name, count=len(results))
                except Exception as exc:
                    log.warning("discover.tool_failed", source=f"web/{adapter_name}", error=str(exc))
                    results = []

                for r in results:
                    url = getattr(r, "url", None)
                    if not url:
                        continue
                    if url in existing_url_to_id:
                        # Re-use: load existing link for this campaign
                        reused_links.append(Link(
                            id=existing_url_to_id[url],
                            tenant_id=tenant_id,
                            url=url,
                            source=LinkSourceModel.web,
                        ))
                    elif url not in seen_urls:
                        seen_urls.add(url)
                        raw_links.append(Link(
                            id=_new_id(),
                            tenant_id=tenant_id,
                            campaign_id=campaign_id,
                            url=url,
                            source=LinkSourceModel.web,
                        ))

        elif source_name in non_web_source_map:
            tool_fn, lnk_source = non_web_source_map[source_name]
            try:
                results = tool_fn(**base_kwargs)
            except Exception as exc:
                log.warning("discover.tool_failed", source=source_name, error=str(exc))
                results = []

            for r in results:
                url = getattr(r, "url", None)
                if not url:
                    continue
                if url in existing_url_to_id:
                    reused_links.append(Link(
                        id=existing_url_to_id[url],
                        tenant_id=tenant_id,
                        url=url,
                        source=lnk_source,
                    ))
                elif url not in seen_urls:
                    seen_urls.add(url)
                    raw_links.append(Link(
                        id=_new_id(),
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        url=url,
                        source=lnk_source,
                    ))

    raw_links = raw_links[: disc.volume_per_run]

    if raw_links:
        try:
            with create_db_session() as session:
                for lnk in raw_links:
                    row = LinkRow(
                        id=lnk.id,
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        url=lnk.url,
                        source=lnk.source.value,
                    )
                    session.add(row)
                    write_event(
                        db=session,
                        event_type="link.discovered",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=None,
                        payload={"url": lnk.url, "source": lnk.source.value},
                    )
        except Exception as exc:
            log.warning("discover.db_write_failed", error=str(exc))

    all_new = list(state.get("links", [])) + raw_links + reused_links
    return {"links": all_new}


# ---------------------------------------------------------------------------
# scrape_links  →  fills link.page_text
# ---------------------------------------------------------------------------

def node_scrape_links(state: AgentState) -> dict:
    """Scrape each link and store page_text on the Link and in LinkRow."""
    if state.get("error"):
        return {}

    updated: list[Link] = []
    for lnk in state.get("links", []):
        if lnk.page_text:
            updated.append(lnk)
            continue
        try:
            text = scrape_page(url=lnk.url)
            now = _now()
            excerpt = text[:500] if text else None
            scraped = lnk.model_copy(update={"page_text": text, "page_excerpt": excerpt, "scraped_at": now})
            updated.append(scraped)
            try:
                with create_db_session() as session:
                    row = (
                        session.query(LinkRow)
                        .filter(LinkRow.id == lnk.id, LinkRow.tenant_id == lnk.tenant_id)
                        .first()
                    )
                    if row:
                        row.page_text = text
                        row.page_excerpt = excerpt
                        row.scraped_at = now
            except Exception as exc:
                log.warning("scrape_links.db_write_failed", link_id=lnk.id, error=str(exc))
        except Exception as exc:
            log.warning("scrape_links.failed", link_id=lnk.id, url=lnk.url, error=str(exc))
            updated.append(lnk)

    return {"links": updated}


# ---------------------------------------------------------------------------
# identify_leads  →  extracts Lead entities from scraped pages
# ---------------------------------------------------------------------------

def node_identify_leads(state: AgentState) -> dict:
    """Use LLM to identify company entities on each scraped page."""
    if state.get("error"):
        return {}

    config = state["config"]
    llm = LLMClient()
    new_leads: list[Lead] = []
    tenant_id = state["tenant_id"]
    campaign_id = state["campaign_id"]

    # Build set of domains already in DB for this campaign (dedup guard)
    existing_domains: set[str] = set()
    try:
        with create_db_session() as db_check:
            rows = (
                db_check.query(LeadRow.domain)
                .filter(LeadRow.tenant_id == tenant_id, LeadRow.campaign_id == campaign_id, LeadRow.domain.isnot(None))
                .all()
            )
            existing_domains = {r[0] for r in rows}
    except Exception as exc:
        log.warning("identify_leads.domain_dedup_failed", error=str(exc))

    for lnk in state.get("links", []):
        if not lnk.page_text:
            continue
        # Skip links already processed in a previous run
        if lnk.identified_at is not None:
            continue
        try:
            leads = identify_leads(link=lnk, icp=config.icp, llm=llm, config=config)
            for lead in leads:
                if lead.domain and lead.domain in existing_domains:
                    log.info("identify_leads.domain_skip", domain=lead.domain, link_id=lnk.id)
                    continue
                if lead.domain:
                    existing_domains.add(lead.domain)
                new_leads.append(lead)
                try:
                    with create_db_session() as session:
                        # Upsert CompanyRow for this domain (tenant-wide)
                        company_id: str | None = None
                        if lead.domain:
                            company_row = (
                                session.query(CompanyRow)
                                .filter(CompanyRow.tenant_id == tenant_id, CompanyRow.domain == lead.domain)
                                .first()
                            )
                            if company_row is None:
                                company_row = CompanyRow(
                                    id=_new_id(),
                                    tenant_id=tenant_id,
                                    domain=lead.domain,
                                    company_name=lead.company_name,
                                    industry=lead.industry,
                                    headcount_range=lead.headcount_range,
                                    business_type=lead.business_type,
                                    first_seen_at=_now(),
                                )
                                session.add(company_row)
                            else:
                                # Fill nulls only — never overwrite existing agent/human data
                                if company_row.company_name is None and lead.company_name:
                                    company_row.company_name = lead.company_name
                                if company_row.industry is None and lead.industry:
                                    company_row.industry = lead.industry
                                if company_row.headcount_range is None and lead.headcount_range:
                                    company_row.headcount_range = lead.headcount_range
                                if company_row.business_type is None and lead.business_type:
                                    company_row.business_type = lead.business_type
                            session.flush()
                            company_id = company_row.id

                        row = LeadRow(
                            id=lead.id,
                            tenant_id=tenant_id,
                            campaign_id=campaign_id,
                            link_id=lnk.id,
                            company_id=company_id,
                            stage=LeadStage.prospect.value,
                            company_name=lead.company_name,
                            domain=lead.domain,
                            industry=lead.industry,
                            headcount_range=lead.headcount_range,
                            business_type=lead.business_type,
                        )
                        session.add(row)

                        # Stamp identified_at on the link
                        link_row = (
                            session.query(LinkRow)
                            .filter(LinkRow.id == lnk.id, LinkRow.tenant_id == tenant_id)
                            .first()
                        )
                        if link_row:
                            link_row.identified_at = _now()

                        write_event(
                            db=session,
                            event_type="lead.identified",
                            tenant_id=tenant_id,
                            campaign_id=campaign_id,
                            lead_id=lead.id,
                            payload={"company_name": lead.company_name, "link_id": lnk.id, "company_id": company_id},
                        )

                        # Write link_leads junction row
                        ll_row = LinkLeadsRow(
                            id=_new_id(),
                            tenant_id=tenant_id,
                            link_id=lnk.id,
                            lead_id=lead.id,
                            campaign_id=campaign_id,
                        )
                        session.add(ll_row)
                except Exception as exc:
                    log.warning("identify_leads.db_write_failed", lead_id=lead.id, error=str(exc))
        except Exception as exc:
            log.warning("identify_leads.link_failed", link_id=lnk.id, error=str(exc))

    return {"leads": list(state.get("leads", [])) + new_leads}


# ---------------------------------------------------------------------------
# research  →  cumulative enrichment
# ---------------------------------------------------------------------------

def node_research(state: AgentState) -> dict:
    """Research each prospect via independent web search, then synthesise.

    Sub-step 3A: web-search the company → scrape result pages.
    Sub-step 3B: call enrich_lead with scraped research_sources.
    Sub-step 3C: append results to lead + company (cumulative).

    Spec: spec/product/04-capabilities/02-enrichment.md — Sub-step 3
    """
    if state.get("error"):
        return {}

    config = state["config"]
    llm = LLMClient()
    updated_leads: list[Lead] = []

    try:
        from zer0.config.settings import get_settings
        settings = get_settings()
        tavily_key = settings.tavily_api_key
    except Exception:
        tavily_key = None

    for lead in state.get("leads", []):
        if lead.stage not in (LeadStage.prospect, LeadStage.research):
            updated_leads.append(lead)
            continue
        try:
            # 3A — Independent web search for this company
            research_sources: list[str] = []
            query_str = f"{lead.company_name or ''} {lead.domain or ''} company overview".strip()

            if tavily_key:
                from zer0.tools.web_search import web_search as _tavily_search
                from zer0.domain.config import DiscoveryConfig, DiscoverySource
                research_disc = DiscoveryConfig(
                    sources=[DiscoverySource.web],
                    query_templates=[query_str],
                    geography=[],
                    volume_per_run=5,
                )
                try:
                    res = _tavily_search(
                        discovery_config=research_disc,
                        icp=config.icp,
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id or state["campaign_id"],
                        tavily_api_key=tavily_key,
                    )
                    research_urls = [getattr(r, "url", None) for r in res if getattr(r, "url", None)]
                except Exception as exc:
                    log.warning("research.tavily_failed", lead_id=lead.id, error=str(exc))
                    research_urls = []
            else:
                from zer0.tools.duckduckgo_search import duckduckgo_search as _ddg
                from duckduckgo_search import DDGS
                try:
                    with DDGS() as ddgs:
                        ddg_results = list(ddgs.text(query_str, max_results=5))
                    research_urls = [r.get("href") for r in ddg_results if r.get("href")]
                except Exception as exc:
                    log.warning("research.ddg_failed", lead_id=lead.id, error=str(exc))
                    research_urls = []

            for url in research_urls[:5]:
                try:
                    text = scrape_page(url=url)
                    if text:
                        research_sources.append(text)
                except Exception as exc:
                    log.debug("research.scrape_skipped", url=url, error=str(exc))

            # 3B — Synthesise via LLM
            enriched = enrich_lead(
                lead=lead,
                research_sources=research_sources,
                icp=config.icp,
                llm=llm,
                config=config,
            )
            updated = enriched.model_copy(update={"stage": LeadStage.research})
            updated_leads.append(updated)

            # 3C — Cumulative write to lead + company
            try:
                with create_db_session() as session:
                    row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead.id, LeadRow.tenant_id == lead.tenant_id)
                        .first()
                    )
                    if row:
                        row.stage = LeadStage.research.value
                        row.research_summary = updated.research_summary
                        row.signals = updated.signals
                        row.last_researched_at = updated.last_researched_at

                    if lead.domain:
                        company_row = (
                            session.query(CompanyRow)
                            .filter(CompanyRow.tenant_id == lead.tenant_id, CompanyRow.domain == lead.domain)
                            .first()
                        )
                        if company_row:
                            if updated.research_summary:
                                if company_row.research_summary:
                                    company_row.research_summary = (
                                        company_row.research_summary + "\n\n---\n" + updated.research_summary
                                    )
                                else:
                                    company_row.research_summary = updated.research_summary
                            if updated.signals:
                                existing = set(company_row.signals or [])
                                merged = list(existing | set(updated.signals))
                                company_row.signals = merged
                            company_row.last_enriched_at = _now()

                    write_event(
                        db=session,
                        event_type="lead.researched",
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id or state["campaign_id"],
                        lead_id=lead.id,
                        payload={"signals_count": len(updated.signals or []), "sources_used": len(research_sources)},
                    )
            except Exception as exc:
                log.warning("research.db_write_failed", lead_id=lead.id, error=str(exc))

        except Exception as exc:
            log.warning("research.lead_failed", lead_id=lead.id, error=str(exc))
            updated_leads.append(lead)

    return {"leads": updated_leads}


# ---------------------------------------------------------------------------
# qualify
# ---------------------------------------------------------------------------

def node_qualify(state: AgentState) -> dict:
    """Score leads; persist stage, score, and rationale to DB."""
    if state.get("error"):
        return {}

    config = state["config"]
    llm = LLMClient()
    updated_leads: list[Lead] = []

    for lead in state.get("leads", []):
        if lead.stage != LeadStage.research:
            updated_leads.append(lead)
            continue
        try:
            result = qualify_lead(
                lead=lead,
                qualification_config=config.qualification_config,
                llm=llm,
                config=config,
            )
            updated_leads.append(result)

            db_stage = result.stage.value
            event_type = "lead.qualified" if result.stage == LeadStage.qualification else "lead.rejected"

            try:
                with create_db_session() as session:
                    row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead.id, LeadRow.tenant_id == lead.tenant_id)
                        .first()
                    )
                    if row:
                        row.stage = db_stage
                        row.score = result.score
                        row.per_criterion_scores = [s.model_dump() for s in result.per_criterion_scores]
                        row.rationale = result.rationale
                        row.rejection_reason = result.rejection_reason
                    write_event(
                        db=session,
                        event_type=event_type,
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        payload={"stage": db_stage, "score": result.score},
                    )
            except Exception as exc:
                log.warning("qualify.db_write_failed", lead_id=lead.id, error=str(exc))

        except Exception as exc:
            log.warning("qualify.lead_failed", lead_id=lead.id, error=str(exc))
            updated_leads.append(lead)

    return {"leads": updated_leads}


# ---------------------------------------------------------------------------
# get_people
# ---------------------------------------------------------------------------

def node_get_people(state: AgentState) -> dict:
    """Discover people at all qualified leads."""
    if state.get("error"):
        return {}

    config = state["config"]
    new_people: list[Person] = []
    updated_leads: list[Lead] = []

    for lead in state.get("leads", []):
        if lead.stage != LeadStage.qualification:
            updated_leads.append(lead)
            continue
        try:
            people = find_all_people(
                lead=lead,
                target_roles=config.icp.target_roles,
                config=config,
            )
            for person in people:
                # Deduplicate: if same (company_id, email) exists, skip insert
                company_id_for_lead = None
                if lead.company_id:
                    company_id_for_lead = lead.company_id
                    # Check if this person already exists for this company
                    try:
                        with create_db_session() as dup_check:
                            existing = (
                                dup_check.query(PersonRow)
                                .filter(
                                    PersonRow.company_id == company_id_for_lead,
                                    PersonRow.email == person.email,
                                )
                                .first()
                            )
                            if existing:
                                log.info(
                                    "get_people.cross_campaign_dedup",
                                    person_id=existing.id,
                                    company_id=company_id_for_lead,
                                )
                                new_people.append(person.model_copy(update={
                                    "id": existing.id,
                                    "company_id": company_id_for_lead,
                                }))
                                continue
                    except Exception as exc:
                        log.warning("get_people.dedup_check_failed", error=str(exc))

                person_with_company = person.model_copy(update={"company_id": company_id_for_lead})
                new_people.append(person_with_company)
                try:
                    with create_db_session() as session:
                        row = PersonRow(
                            id=person.id,
                            tenant_id=lead.tenant_id,
                            lead_id=lead.id,
                            company_id=company_id_for_lead,
                            first_name=person.first_name,
                            last_name=person.last_name,
                            full_name=person.full_name,
                            email=person.email,
                            phone=person.phone,
                            role=person.role,
                            linkedin_url=person.linkedin_url,
                        )
                        session.add(row)
                        write_event(
                            db=session,
                            event_type="person.discovered",
                            tenant_id=lead.tenant_id,
                            campaign_id=lead.campaign_id or state["campaign_id"],
                            lead_id=lead.id,
                            person_id=person.id,
                            payload={"role": person.role},
                        )
                except Exception as exc:
                    log.warning("get_people.db_write_failed", person_id=person.id, error=str(exc))

            updated_lead = lead.model_copy(update={"stage": LeadStage.people})
            updated_leads.append(updated_lead)

            try:
                with create_db_session() as session:
                    row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead.id, LeadRow.tenant_id == lead.tenant_id)
                        .first()
                    )
                    if row:
                        row.stage = LeadStage.people.value
                    write_event(
                        db=session,
                        event_type="lead.people_found",
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        payload={"count": len(people)},
                    )
            except Exception as exc:
                log.warning("get_people.lead_stage_failed", lead_id=lead.id, error=str(exc))

        except Exception as exc:
            log.warning("get_people.lead_failed", lead_id=lead.id, error=str(exc))
            updated_leads.append(lead)

    return {
        "leads": updated_leads,
        "people": list(state.get("people", [])) + new_people,
    }


# ---------------------------------------------------------------------------
# approval_gate  →  approves people for outreach
# ---------------------------------------------------------------------------

def node_approval_gate(state: AgentState) -> dict:
    """Route people to outreach or park for human approval.

    Auto modes: person.approved_for_outreach = True immediately.
    Human modes: park and notify via Slack.
    """
    if state.get("error"):
        return {}

    config = state["config"]
    leads_with_people_stage = [l for l in state.get("leads", []) if l.stage == LeadStage.people]
    lead_ids = {l.id for l in leads_with_people_stage}
    people = [p for p in state.get("people", []) if p.lead_id in lead_ids]
    tenant_id = state["tenant_id"]
    campaign_id = state["campaign_id"]

    auto_modes = {ApprovalMode.full_auto, ApprovalMode.approve_messages}
    person_ids = [p.id for p in people]

    if config.approval_mode in auto_modes:
        approved_people: list[Person] = []
        if person_ids:
            try:
                with create_db_session() as session:
                    for person in people:
                        row = (
                            session.query(PersonRow)
                            .filter(PersonRow.id == person.id, PersonRow.lead_id == person.lead_id)
                            .first()
                        )
                        if row:
                            row.approved_for_outreach = True
                        write_event(
                            db=session,
                            event_type="approval.granted",
                            tenant_id=tenant_id,
                            campaign_id=campaign_id,
                            lead_id=person.lead_id,
                            person_id=person.id,
                            payload={"auto": True},
                        )
                    # Auto-approved leads proceed directly to outreach.
                    for lead in leads_with_people_stage:
                        lead_row = (
                            session.query(LeadRow)
                            .filter(LeadRow.id == lead.id, LeadRow.tenant_id == tenant_id)
                            .first()
                        )
                        if lead_row:
                            lead_row.stage = LeadStage.outreach.value
            except Exception as exc:
                log.warning("approval_gate.auto_approve_failed", error=str(exc))
            approved_people = [p.model_copy(update={"approved_for_outreach": True}) for p in people]

        updated_leads = [
            l.model_copy(update={"stage": LeadStage.outreach}) if l.id in lead_ids else l
            for l in state.get("leads", [])
        ]
        all_people = [
            p.model_copy(update={"approved_for_outreach": True}) if p.id in {ap.id for ap in approved_people} else p
            for p in state.get("people", [])
        ]
        return {
            "leads": updated_leads,
            "people": all_people,
            "approved_person_ids": person_ids,
        }

    # Human approval required
    if person_ids:
        try:
            with create_db_session() as session:
                for lead in leads_with_people_stage:
                    lead_row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead.id, LeadRow.tenant_id == tenant_id)
                        .first()
                    )
                    if lead_row:
                        lead_row.stage = LeadStage.approval.value
                for person in people:
                    write_event(
                        db=session,
                        event_type="approval.pending",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=person.lead_id,
                        person_id=person.id,
                        payload={},
                    )
        except Exception as exc:
            log.warning("approval_gate.pending_event_failed", error=str(exc))

        if config.slack_webhook_url:
            post_slack_event(
                webhook_url=config.slack_webhook_url,
                event_type="approval.pending",
                tenant_id=tenant_id,
                payload={"pending_count": len(person_ids), "campaign_id": campaign_id},
            )

    updated_leads = [
        l.model_copy(update={"stage": LeadStage.approval}) if l.id in lead_ids else l
        for l in state.get("leads", [])
    ]
    return {
        "leads": updated_leads,
        "pending_approval_person_ids": person_ids,
        "approved_person_ids": [],
    }


# ---------------------------------------------------------------------------
# outreach  →  draft and send per approved person
# ---------------------------------------------------------------------------

def node_outreach(state: AgentState) -> dict:
    """Draft and (optionally) send first-touch messages for each approved person."""
    if state.get("error"):
        return {}

    config = state["config"]
    llm = LLMClient()
    approved_ids = set(state.get("approved_person_ids", []))
    leads_map = {l.id: l for l in state.get("leads", [])}
    people_map = {p.id: p for p in state.get("people", [])}

    drafts = []
    sent = []
    approval_required = config.approval_mode in {ApprovalMode.approve_messages, ApprovalMode.approve_all}
    channels = config.outreach_config.channels_enabled

    for person_id in approved_ids:
        person = people_map.get(person_id)
        if not person:
            continue
        lead = leads_map.get(person.lead_id)
        if not lead:
            continue

        for channel in channels:
            try:
                lang = detect_language(lead=lead, llm=llm, config=config)
                if lang and not lead.detected_language:
                    lead = lead.model_copy(update={"detected_language": lang})

                msg_draft = draft_outreach(
                    lead=lead,
                    person=person,
                    channel=channel,
                    sequence_number=1,
                    llm=llm,
                    config=config,
                )
                drafts.append(msg_draft)

                with create_db_session() as session:
                    lead_row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead.id, LeadRow.tenant_id == lead.tenant_id)
                        .first()
                    )
                    if lead_row and lang:
                        lead_row.detected_language = lang

                    msg_status = "pending_approval" if approval_required else "drafted"
                    msg_row = MessageRow(
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        person_id=person.id,
                        channel=channel.value,
                        subject=msg_draft.subject,
                        body=msg_draft.body,
                        personalisation_notes=msg_draft.personalisation_notes,
                        config_snapshot=config.model_dump(),
                        sequence_number=1,
                        status=msg_status,
                    )
                    session.add(msg_row)
                    session.flush()

                    write_event(
                        db=session,
                        event_type="message.drafted",
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        person_id=person.id,
                        payload={"channel": channel.value, "sequence": 1, "message_id": msg_row.id},
                    )

                    if approval_required:
                        write_event(
                            db=session,
                            event_type="message.pending_approval",
                            tenant_id=lead.tenant_id,
                            campaign_id=lead.campaign_id,
                            lead_id=lead.id,
                            person_id=person.id,
                            payload={"message_id": msg_row.id},
                        )
                        continue

                    sm = _send_message(msg_draft=msg_draft, config=config, lead=lead, person=person)
                    sent.append(sm)

                    msg_row.status = "sent"
                    msg_row.sent_at = sm.sent_at
                    msg_row.external_message_id = sm.external_message_id
                    if lead_row:
                        lead_row.stage = LeadStage.outreach.value

                    write_event(
                        db=session,
                        event_type="message.sent",
                        tenant_id=lead.tenant_id,
                        campaign_id=lead.campaign_id,
                        lead_id=lead.id,
                        person_id=person.id,
                        payload={"channel": channel.value, "sequence": 1},
                    )

            except Exception as exc:
                log.warning(
                    "outreach.person_failed",
                    person_id=person_id,
                    channel=channel.value if hasattr(channel, "value") else str(channel),
                    error=str(exc),
                )

    if approval_required and drafts and config.slack_webhook_url:
        post_slack_event(
            webhook_url=config.slack_webhook_url,
            event_type="message.pending_approval",
            tenant_id=state["tenant_id"],
            payload={"pending_count": len(drafts), "campaign_id": state["campaign_id"]},
        )

    return {
        "outreach_drafts": list(state.get("outreach_drafts", [])) + drafts,
        "sent_messages": list(state.get("sent_messages", [])) + sent,
    }


def _send_message(*, msg_draft, config, lead, person) -> SentMessage:
    """Call the appropriate send tool and return a SentMessage."""
    from zer0.config.settings import get_settings

    settings = get_settings()
    enc_key = settings.credential_encryption_key.encode()

    if msg_draft.channel == Channel.email:
        return send_email(
            draft=msg_draft,
            encrypted_credentials=(
                config.google_oauth_token_enc.encode() if config.google_oauth_token_enc else b""
            ),
            encryption_key=enc_key,
        )
    else:
        return send_whatsapp(
            draft=msg_draft,
            recipient_phone=person.phone or "",
            encrypted_credentials=(
                config.whatsapp_api_key_enc.encode() if config.whatsapp_api_key_enc else b""
            ),
            encryption_key=enc_key,
        )


# ---------------------------------------------------------------------------
# check_replies  →  handles positive replies, stops sibling people, sends follow-ups
# ---------------------------------------------------------------------------

def node_check_replies(state: AgentState) -> dict:
    """Check replies and send follow-ups for active leads.

    Positive reply from person A → stop outreach to all sibling people,
    set lead.stage = first_contact.
    All follow-ups exhausted with no reply → lead.stage = no_contact.
    """
    if state.get("error"):
        return {}

    config = state["config"]
    now = _now()
    completed = list(state.get("completed_lead_ids", []))
    new_replies = []
    new_sent: list[SentMessage] = []
    tenant_id = state["tenant_id"]
    campaign_id = state["campaign_id"]

    try:
        from zer0.config.settings import get_settings

        settings = get_settings()
        enc_key = settings.credential_encryption_key.encode()
        replies = check_replies(
            campaign_id=campaign_id,
            tenant_id=tenant_id,
            channels=config.outreach_config.channels_enabled,
            encrypted_credentials=(
                config.google_oauth_token_enc.encode() if config.google_oauth_token_enc else b""
            ),
            encryption_key=enc_key,
        )
        new_replies.extend(replies)

        positive_lead_ids = {
            r.lead_id for r in replies if r.sentiment and r.sentiment.value == "positive"
        }
        for lid in positive_lead_ids:
            if lid in completed:
                continue
            completed.append(lid)
            try:
                with create_db_session() as session:
                    # Stop all sibling people for this lead
                    session.query(PersonRow).filter(PersonRow.lead_id == lid).update(
                        {"outreach_stopped": True}
                    )
                    lead_row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lid, LeadRow.tenant_id == tenant_id)
                        .first()
                    )
                    if lead_row:
                        lead_row.stage = LeadStage.first_contact.value
                    write_event(
                        db=session,
                        event_type="handoff.triggered",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lid,
                        payload={"reason": "positive_reply"},
                    )
            except Exception as exc:
                log.warning("check_replies.handoff_db_failed", lead_id=lid, error=str(exc))

            if config.slack_webhook_url:
                post_slack_event(
                    webhook_url=config.slack_webhook_url,
                    event_type="handoff.triggered",
                    tenant_id=tenant_id,
                    payload={"lead_id": lid, "campaign_id": campaign_id},
                )

    except Exception as exc:
        log.warning("check_replies.check_failed", error=str(exc))

    # Send follow-ups
    completed_set = set(completed)
    llm = LLMClient()
    leads_map = {l.id: l for l in state.get("leads", [])}
    people_map = {p.id: p for p in state.get("people", [])}
    max_follow_ups = config.outreach_config.follow_up_count

    last_sent_by_person: dict[str, SentMessage] = {}
    for m in state.get("sent_messages", []):
        person_id = getattr(m, "person_id", None)
        if person_id and (
            person_id not in last_sent_by_person
            or m.sequence_number > last_sent_by_person[person_id].sequence_number
        ):
            last_sent_by_person[person_id] = m

    for person_id, last_msg in last_sent_by_person.items():
        person = people_map.get(person_id)
        if not person or person.outreach_stopped:
            continue
        lead_id = person.lead_id
        if lead_id in completed_set:
            continue
        if last_msg.sent_at is None:
            continue
        elapsed_days = (now - last_msg.sent_at).days
        if elapsed_days < config.outreach_config.follow_up_spacing_days:
            continue

        next_seq = last_msg.sequence_number + 1
        if next_seq > 1 + max_follow_ups:
            completed.append(lead_id)
            completed_set.add(lead_id)
            try:
                with create_db_session() as session:
                    lead_row = (
                        session.query(LeadRow)
                        .filter(LeadRow.id == lead_id, LeadRow.tenant_id == tenant_id)
                        .first()
                    )
                    if lead_row:
                        lead_row.stage = LeadStage.no_contact.value
                    write_event(
                        db=session,
                        event_type="outreach.exhausted",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lead_id,
                        payload={"follow_up_count": max_follow_ups},
                    )
            except Exception as exc:
                log.warning("check_replies.exhausted_db_failed", lead_id=lead_id, error=str(exc))
            continue

        lead = leads_map.get(lead_id)
        if not lead:
            continue

        for channel in config.outreach_config.channels_enabled:
            try:
                fu_draft = draft_outreach(
                    lead=lead,
                    person=person,
                    channel=channel,
                    sequence_number=next_seq,
                    llm=llm,
                    config=config,
                )
                sm = _send_message(msg_draft=fu_draft, config=config, lead=lead, person=person)
                new_sent.append(sm)

                with create_db_session() as session:
                    msg_row = MessageRow(
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lead.id,
                        person_id=person.id,
                        channel=channel.value,
                        body=fu_draft.body,
                        subject=fu_draft.subject,
                        personalisation_notes=fu_draft.personalisation_notes,
                        config_snapshot=config.model_dump(),
                        sequence_number=next_seq,
                        status="sent",
                        sent_at=sm.sent_at,
                        external_message_id=sm.external_message_id,
                    )
                    session.add(msg_row)
                    write_event(
                        db=session,
                        event_type="message.sent",
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lead.id,
                        person_id=person.id,
                        payload={"channel": channel.value, "sequence": next_seq},
                    )
            except Exception as exc:
                log.warning(
                    "check_replies.send_failed",
                    person_id=person_id,
                    channel=channel.value if hasattr(channel, "value") else str(channel),
                    error=str(exc),
                )

    return {
        "replies": list(state.get("replies", [])) + new_replies,
        "sent_messages": list(state.get("sent_messages", [])) + new_sent,
        "completed_lead_ids": completed,
    }


# ---------------------------------------------------------------------------
# handle_error
# ---------------------------------------------------------------------------

def node_handle_error(state: AgentState) -> dict:
    """Write error event to audit log and post Slack alert if configured."""
    err = state.get("error", "unknown error")
    log.error("agent.run_failed", error=err)
    try:
        with create_db_session() as session:
            write_event(
                db=session,
                event_type="run.error",
                tenant_id=state.get("tenant_id", ""),
                campaign_id=state.get("campaign_id"),
                lead_id=None,
                payload={"error": err},
            )
    except Exception as exc:
        log.warning("handle_error.db_write_failed", error=str(exc))

    if state.get("config") and getattr(state["config"], "slack_webhook_url", None):
        post_slack_event(
            webhook_url=state["config"].slack_webhook_url,
            event_type="run.error",
            tenant_id=state.get("tenant_id", ""),
            payload={"error": err},
        )
    return {}

