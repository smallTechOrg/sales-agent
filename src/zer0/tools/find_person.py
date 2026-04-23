"""find_person tool.

Spec: spec/product/02-architecture.md — Tools table
Input:  company URL + ICP.target_roles (list[str])
Output: person fields (name, email, phone, role) merged into RawLead
"""

from __future__ import annotations

from pydantic import BaseModel


class PersonDetails(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None


def find_person(
    *,
    company_url: str,
    target_roles: list[str],
) -> PersonDetails:
    """Find decision-maker details for a company.

    TODO: Integrate with Hunter.io / Apollo / LinkedIn People search.
    Returns the best-match person for the given target roles.
    """
    raise NotImplementedError("find_person — integration not implemented")