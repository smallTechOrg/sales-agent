"""Rename customers/contacts to companies/people.

Spec refs:
  - spec/product/07-data-model.md
  - spec/product/09-api.md

This migration keeps existing data and renames the physical schema to match the
runtime ORM and API terminology:
- customers -> companies
- contacts -> people
- *_customer_id -> *_company_id
- *_contact_id -> *_person_id
"""

from __future__ import annotations

from typing import Sequence

from alembic import op

revision: str = "0007_rename_customers_contacts_to_companies_people"
down_revision: str | None = "0006_spec_alignment_columns"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _rename_constraint(table: str, old_name: str, new_name: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = '{old_name}'
            ) THEN
                EXECUTE 'ALTER TABLE {table} RENAME CONSTRAINT {old_name} TO {new_name}';
            END IF;
        END $$;
        """
    )


def _rename_index(old_name: str, new_name: str) -> None:
    op.execute(f"ALTER INDEX IF EXISTS {old_name} RENAME TO {new_name}")


def upgrade() -> None:
    op.rename_table("customers", "companies")
    op.rename_table("contacts", "people")

    op.alter_column("leads", "customer_id", new_column_name="company_id")
    op.alter_column("people", "customer_id", new_column_name="company_id")
    op.alter_column("messages", "contact_id", new_column_name="person_id")
    op.alter_column("replies", "contact_id", new_column_name="person_id")
    op.alter_column("events", "contact_id", new_column_name="person_id")

    _rename_constraint("companies", "uq_customers_tenant_domain", "uq_companies_tenant_domain")
    _rename_constraint("leads", "leads_customer_id_fkey", "leads_company_id_fkey")
    _rename_constraint("people", "contacts_lead_id_fkey", "people_lead_id_fkey")
    _rename_constraint("people", "contacts_customer_id_fkey", "people_company_id_fkey")
    _rename_constraint("messages", "messages_contact_id_fkey", "messages_person_id_fkey")
    _rename_constraint("replies", "replies_contact_id_fkey", "replies_person_id_fkey")
    _rename_constraint("events", "events_contact_id_fkey", "events_person_id_fkey")
    _rename_constraint("people", "uq_contacts_customer_email", "uq_people_company_email")

    _rename_index("ix_leads_customer_id", "ix_leads_company_id")
    _rename_index("idx_contacts_customer", "idx_people_company")
    _rename_index("ix_messages_contact_id", "ix_messages_person_id")
    _rename_index("ix_replies_contact_id", "ix_replies_person_id")
    _rename_index("ix_events_contact_id", "ix_events_person_id")


def downgrade() -> None:
    _rename_index("ix_events_person_id", "ix_events_contact_id")
    _rename_index("ix_replies_person_id", "ix_replies_contact_id")
    _rename_index("ix_messages_person_id", "ix_messages_contact_id")
    _rename_index("idx_people_company", "idx_contacts_customer")
    _rename_index("ix_leads_company_id", "ix_leads_customer_id")

    _rename_constraint("people", "uq_people_company_email", "uq_contacts_customer_email")
    _rename_constraint("events", "events_person_id_fkey", "events_contact_id_fkey")
    _rename_constraint("replies", "replies_person_id_fkey", "replies_contact_id_fkey")
    _rename_constraint("messages", "messages_person_id_fkey", "messages_contact_id_fkey")
    _rename_constraint("people", "people_company_id_fkey", "contacts_customer_id_fkey")
    _rename_constraint("people", "people_lead_id_fkey", "contacts_lead_id_fkey")
    _rename_constraint("leads", "leads_company_id_fkey", "leads_customer_id_fkey")
    _rename_constraint("companies", "uq_companies_tenant_domain", "uq_customers_tenant_domain")

    op.alter_column("events", "person_id", new_column_name="contact_id")
    op.alter_column("replies", "person_id", new_column_name="contact_id")
    op.alter_column("messages", "person_id", new_column_name="contact_id")
    op.alter_column("people", "company_id", new_column_name="customer_id")
    op.alter_column("leads", "company_id", new_column_name="customer_id")

    op.rename_table("people", "contacts")
    op.rename_table("companies", "customers")
