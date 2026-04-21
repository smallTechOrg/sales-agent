"use client";

import { useState, use } from "react";
import { useLeads } from "@/hooks/useLeads";
import { LeadFilterBar, LeadTable } from "@/components/lead/LeadTable";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";

export default function CampaignLeadPipelinePage({
  params,
}: {
  params: Promise<{ tenantId: string; campaignId: string }>;
}) {
  const { tenantId, campaignId } = use(params);
  const [stage, setStage] = useState("");
  const { leads, loading, error } = useLeads({ tenantId, campaignId, stage });

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-2">Lead Pipeline</h1>
      <p className="text-sm text-slate-500 mb-6 font-mono">{campaignId}</p>

      {error && <ErrorBanner message={error} />}

      <LeadFilterBar stage={stage} onStageChange={setStage} />

      {loading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : (
        <LeadTable leads={leads} tenantId={tenantId} />
      )}
    </div>
  );
}
