"use client";

import { useEffect, useState, use } from "react";
import { api, type Lead, ApiError } from "@/lib/api";
import { LeadProfile } from "@/components/lead/LeadProfile";
import { QualificationScores } from "@/components/lead/QualificationScores";
import { LeadMessagesSection } from "@/components/lead/LeadMessagesSection";
import { LeadEventsSection } from "@/components/lead/LeadEventsSection";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";

export default function LeadDetailPage({
  params,
}: {
  params: Promise<{ tenantId: string; leadId: string }>;
}) {
  const { tenantId, leadId } = use(params);
  const [lead, setLead] = useState<Lead | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getLead(tenantId, leadId)
      .then(setLead)
      .catch((e) => setError(e instanceof ApiError ? e.message : String(e)));
  }, [tenantId, leadId]);

  if (error) return <ErrorBanner message={error} />;
  if (!lead)
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <LeadProfile lead={lead} />
      <QualificationScores lead={lead} />
      <LeadMessagesSection tenantId={tenantId} leadId={leadId} />
      <LeadEventsSection tenantId={tenantId} leadId={leadId} />
    </div>
  );
}
