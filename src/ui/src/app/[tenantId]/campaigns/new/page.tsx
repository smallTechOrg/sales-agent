"use client";

import { useState, use } from "react";
import { useRouter } from "next/navigation";
import { CampaignForm, type CampaignState } from "@/components/forms/CampaignForm";
import { useOfferings } from "@/hooks/useOfferings";
import { api } from "@/lib/api";
import { ErrorBanner } from "@/components/ui/ErrorBanner";

export default function NewCampaignPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const router = useRouter();
  const { offerings } = useOfferings(tenantId);
  const [campaign, setCampaign] = useState<CampaignState>({
    name: "",
    offering_id: "",
    approval_mode: "full_auto",
    discovery_sources: "web",
    qualification_threshold: 60,
    outreach_channels: "email",
    follow_up_count: 2,
    follow_up_spacing_days: 3,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof CampaignState, string>>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  const handleSave = async () => {
    const errs: Partial<Record<keyof CampaignState, string>> = {};
    if (!campaign.name.trim()) errs.name = "Required.";
    if (!campaign.offering_id) errs.offering_id = "Required.";
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }
    setSaving(true);
    setSaveError("");
    try {
      const created = await api.createCampaign(tenantId, {
        name: campaign.name,
        offering_id: campaign.offering_id,
        approval_mode: campaign.approval_mode,
        discovery_override: {
          sources: campaign.discovery_sources.split(",").map((s) => s.trim()),
        },
        qualification_override: {
          score_threshold: campaign.qualification_threshold,
        },
        outreach_override: {
          channels_enabled: campaign.outreach_channels.split(",").map((s) => s.trim()),
          follow_up_count: campaign.follow_up_count,
          follow_up_spacing_days: campaign.follow_up_spacing_days,
        },
      });
      router.push(`/${tenantId}/campaigns/${created.id}`);
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">New Campaign</h1>
      {saveError && <ErrorBanner message={saveError} />}
      <CampaignForm
        value={campaign}
        onChange={setCampaign}
        offerings={offerings}
        errors={errors}
      />
      <div className="flex gap-3 mt-8">
        <button
          onClick={() => router.back()}
          className="rounded-md bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-600"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={saving}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          {saving ? "Saving…" : "Create Campaign"}
        </button>
      </div>
    </div>
  );
}
