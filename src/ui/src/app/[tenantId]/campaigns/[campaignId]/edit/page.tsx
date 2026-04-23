"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { CampaignForm, CampaignState } from "@/components/forms/CampaignForm";
import { useOfferings } from "@/hooks/useOfferings";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";

export default function EditCampaignPage({
  params,
}: {
  params: Promise<{ tenantId: string; campaignId: string }>;
}) {
  const { tenantId, campaignId } = use(params);
  const router = useRouter();
  const { offerings } = useOfferings(tenantId);
  const [campaign, setCampaign] = useState<CampaignState | null>(null);
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .getCampaign(tenantId, campaignId)
      .then((c) =>
        setCampaign({
          name: c.name,
          offering_id: c.offering_id,
          approval_mode: (c.approval_mode as CampaignState["approval_mode"]) ?? "full_auto",
          discovery_sources:
            (c.discovery_override?.sources as string[] | undefined)?.join(", ") ?? "web",
          qualification_threshold:
            (c.qualification_override?.score_threshold as number | undefined) ?? 60,
          outreach_channels:
            (c.outreach_override?.channels_enabled as string[] | undefined)?.join(", ") ?? "email",
          follow_up_count:
            (c.outreach_override?.follow_up_count as number | undefined) ?? 2,
          follow_up_spacing_days:
            (c.outreach_override?.follow_up_spacing_days as number | undefined) ?? 3,
        })
      )
      .catch((e) => setLoadError(e instanceof ApiError ? e.message : String(e)));
  }, [tenantId, campaignId]);

  async function handleSave() {
    if (!campaign) return;
    setSaveError("");
    setSaving(true);
    try {
      await api.patchCampaign(tenantId, campaignId, {
        name: campaign.name,
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
      router.push(`/${tenantId}/campaigns/${campaignId}`);
    } catch (e) {
      setSaveError(e instanceof ApiError ? e.message : String(e));
      setSaving(false);
    }
  }

  if (loadError) return <ErrorBanner message={loadError} />;
  if (!campaign)
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Edit Campaign</h1>
      {saveError && <ErrorBanner message={saveError} className="mb-4" />}
      <CampaignForm
        value={campaign}
        onChange={setCampaign}
        offerings={offerings}
        errors={{}}      />
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
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 flex items-center gap-2"
        >
          {saving && <Spinner size="sm" />}
          Save changes
        </button>
      </div>
    </div>
  );
}
