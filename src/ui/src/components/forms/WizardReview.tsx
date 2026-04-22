"use client";

import type { CredentialsState } from "./CredentialsForm";
import type { OfferingState } from "./OfferingForm";
import type { CampaignState } from "./CampaignForm";

interface WizardReviewProps {
  tenantName: string;
  credentials: CredentialsState;
  offering: OfferingState;
  campaign: CampaignState;
  onEdit: (step: number) => void;
  onSave: () => void;
  saving: boolean;
  error?: string;
}

function Section({
  title,
  onEdit,
  step,
  children,
}: {
  title: string;
  onEdit: (step: number) => void;
  step: number;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg bg-slate-800 border border-slate-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-white">{title}</h3>
        <button
          onClick={() => onEdit(step)}
          className="text-xs text-indigo-400 hover:text-indigo-300"
        >
          Edit
        </button>
      </div>
      {children}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2 text-sm">
      <span className="text-slate-500 w-40 shrink-0">{label}</span>
      <span className="text-slate-200 break-all">{value || "—"}</span>
    </div>
  );
}

export function WizardReview({
  tenantName,
  credentials,
  offering,
  campaign,
  onEdit,
  onSave,
  saving,
  error,
}: WizardReviewProps) {
  return (
    <div className="flex flex-col gap-5">
      <h2 className="text-lg font-bold text-white">Review</h2>
      <p className="text-sm text-slate-400">
        Review all inputs before saving. Secrets are shown as presence indicators only.
      </p>

      <Section title="Identity" onEdit={onEdit} step={0}>
        <Row label="Tenant name" value={tenantName} />
      </Section>

      <Section title="Credentials" onEdit={onEdit} step={1}>
        <Row label="Gmail token" value={credentials.gmail_token ? "••••••" : "not set"} />
        <Row label="WhatsApp key" value={credentials.whatsapp_key ? "••••••" : "not set"} />
        <Row label="Slack webhook" value={credentials.slack_webhook ? "••••••" : "not set"} />
      </Section>

      <Section title="Offering" onEdit={onEdit} step={2}>
        <Row label="Name" value={offering.name} />
        <Row label="Value proposition" value={offering.value_proposition} />
        <Row label="Industries" value={offering.target_industries} />
        <Row label="Roles" value={offering.target_roles} />
      </Section>

      <Section title="Campaign" onEdit={onEdit} step={3}>
        <Row label="Name" value={campaign.name} />
        <Row label="Approval mode" value={campaign.approval_mode} />
        <Row label="Channels" value={campaign.outreach_channels} />
        <Row label="Follow-ups" value={`${campaign.follow_up_count} × every ${campaign.follow_up_spacing_days}d`} />
      </Section>

      {error && (
        <div className="rounded bg-red-950 border border-red-800 p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <button
        onClick={onSave}
        disabled={saving}
        className="rounded-md bg-indigo-600 px-6 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 self-start"
      >
        {saving ? "Saving…" : "Save & Enable"}
      </button>
    </div>
  );
}
