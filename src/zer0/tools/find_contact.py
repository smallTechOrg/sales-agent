"""find_contact tool.

Spec: spec/product/02-architecture.md — Tools table
Input:  company URL + ICP.target_roles (list[str])
Output: contact fields (name, email, phone, role) merged into RawLead
"""

from __future__ import annotations

from pydantic import BaseModel


class ContactDetails(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None


def find_contact(
    *,
    company_url: str,
    target_roles: list[str],
) -> ContactDetails:
    """Find decision-maker contact details for a company.

    TODO: Integrate with Hunter.io / Apollo / LinkedIn People search.
    Returns best-match contact for the given target roles.
    """
    raise NotImplementedError("find_contact — integration not implemented")
