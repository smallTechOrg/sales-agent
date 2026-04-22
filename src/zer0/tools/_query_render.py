"""Shared query template renderer.

Spec: spec/product/04-capabilities/01-discovery.md — Query templates

Templates use {{variable}} syntax (consistent with prompts/).
Supported variables:

  {{roles}}          — OR-joined target roles        e.g. "CEO OR VP Sales"
  {{industries}}     — OR-joined target industries   e.g. "SaaS OR FinTech"
  {{geography}}      — OR-joined ICP geography       e.g. "United States OR Canada"
  {{keywords}}       — OR-joined keywords            e.g. "B2B OR enterprise"
  {{company_size}}   — "N-M employees" range string  e.g. "10-500 employees"
"""

from __future__ import annotations

from zer0.domain import DiscoveryConfig, ICP


def render_query(template: str, discovery_config: DiscoveryConfig, icp: ICP) -> str:
    size = icp.company_size_range
    replacements = {
        "{{roles}}": " OR ".join(icp.target_roles),
        "{{industries}}": " OR ".join(icp.target_industries),
        "{{geography}}": " OR ".join(icp.geography),
        "{{keywords}}": " OR ".join(icp.keywords),
        "{{company_size}}": f"{size.min}-{size.max} employees",
    }
    query = template
    for placeholder, value in replacements.items():
        query = query.replace(placeholder, value)
    return query.strip()
