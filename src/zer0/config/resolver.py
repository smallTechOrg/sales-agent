"""Config resolution service.

Spec: spec/product/02-architecture.md — Configuration resolution
Spec: spec/product/05-agent-graph.md — resolve_config node

Merges Campaign overrides onto Offering defaults and returns a fully-resolved
ResolvedConfig. Called once at the start of every agent tick — the graph never
reads Campaign or Offering rows directly after this point.
"""

from __future__ import annotations

import os

from cryptography.fernet import Fernet
from pydantic import ValidationError
from sqlalchemy.orm import Session

from zer0.db.models import CampaignRow, OfferingRow, TenantRow
from zer0.domain import (
    ApprovalMode,
    DiscoveryConfig,
    ICP,
    OutreachConfig,
    QualificationConfig,
    ResolvedConfig,
)


def _decrypt_optional(encrypted: str | None) -> str | None:
    """Decrypt a Fernet-encrypted string using ZER0_CREDENTIAL_ENCRYPTION_KEY.

    Returns None if the value is missing or decryption fails.
    """
    if not encrypted:
        return None
    key = os.getenv("ZER0_CREDENTIAL_ENCRYPTION_KEY", "")
    if not key:
        return None
    try:
        return Fernet(key.encode()).decrypt(encrypted.encode()).decode()
    except Exception:
        return None


class ConfigResolutionError(Exception):
    """Raised when a required config field is missing and no default exists."""


class ConfigResolver:
    """Resolves campaign + offering into a single ResolvedConfig.

    Resolution order (spec): Campaign override → Offering default → ValidationError
    There is no silent system default — if a field is unset, this raises.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def resolve(self, campaign_id: str, tenant_id: str) -> ResolvedConfig:
        campaign: CampaignRow | None = (
            self._db.query(CampaignRow)
            .filter(
                CampaignRow.id == campaign_id,
                CampaignRow.tenant_id == tenant_id,
                CampaignRow.deleted_at.is_(None),
            )
            .first()
        )
        if campaign is None:
            raise ConfigResolutionError(
                f"Campaign {campaign_id!r} not found for tenant {tenant_id!r}"
            )

        offering: OfferingRow | None = (
            self._db.query(OfferingRow)
            .filter(
                OfferingRow.id == campaign.offering_id,
                OfferingRow.tenant_id == tenant_id,
                OfferingRow.deleted_at.is_(None),
            )
            .first()
        )
        if offering is None:
            raise ConfigResolutionError(
                f"Offering {campaign.offering_id!r} not found for tenant {tenant_id!r}"
            )

        tenant: TenantRow | None = (
            self._db.query(TenantRow)
            .filter(TenantRow.id == tenant_id, TenantRow.deleted_at.is_(None))
            .first()
        )
        if tenant is None:
            raise ConfigResolutionError(f"Tenant {tenant_id!r} not found")

        discovery = self._merge(
            offering.discovery_config, campaign.discovery_override, DiscoveryConfig,
            "discovery_config", offering.id,
        )
        icp = self._merge(offering.icp, campaign.icp_override, ICP, "icp", offering.id)
        qualification = self._merge(
            offering.qualification_config,
            campaign.qualification_override,
            QualificationConfig,
            "qualification_config",
            offering.id,
        )
        outreach = self._merge(
            offering.outreach_config, campaign.outreach_override, OutreachConfig,
            "outreach_config", offering.id,
        )

        approval_mode: ApprovalMode = (
            ApprovalMode(campaign.approval_mode)
            if campaign.approval_mode
            else ApprovalMode.full_auto
        )

        return ResolvedConfig(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            offering_id=str(offering.id),
            offering_name=offering.name,
            value_proposition=offering.value_proposition or "",
            pain_points=offering.pain_points or [],
            discovery_config=discovery,
            icp=icp,
            qualification_config=qualification,
            outreach_config=outreach,
            approval_mode=approval_mode,
            volume_cap=campaign.volume_cap,
            schedule=campaign.schedule,
            google_oauth_token_enc=tenant.google_oauth_token_enc,
            whatsapp_api_key_enc=tenant.whatsapp_api_key_enc,
            slack_webhook_url=_decrypt_optional(tenant.slack_webhook_url_enc),
        )

    @staticmethod
    def _merge(  # type: ignore[type-arg]
        base: dict,
        override: dict | None,
        model: type,
        block_name: str = "",
        offering_id: object = None,
    ) -> object:
        merged = {**(base or {}), **(override or {})}
        try:
            return model.model_validate(merged)
        except ValidationError as exc:
            label = f"'{block_name}' " if block_name else ""
            location = f" (offering {offering_id})" if offering_id else ""
            raise ConfigResolutionError(
                f"Offering{location} is missing required {label}config fields — "
                f"configure the offering before triggering the campaign.\n{exc}"
            ) from exc
