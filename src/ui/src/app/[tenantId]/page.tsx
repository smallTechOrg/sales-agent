"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { api, type TenantData } from "@/lib/api";
import { useCampaigns } from "@/hooks/useCampaigns";
import { TenantHeader } from "@/components/layout/TenantHeader";
import { CampaignCard } from "@/components/campaign/CampaignCard";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";

export default function TenantDetailPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const [tenant, setTenant] = useState<TenantData | null>(null);
  const [tenantError, setTenantError] = useState("");
  const { campaigns, loading, error, refresh } = useCampaigns(tenantId);

  useEffect(() => {
    api
      .getTenant(tenantId)
      .then(setTenant)
      .catch((e) => setTenantError(String(e)));
  }, [tenantId]);

  const handleDelete = (id: string) => {
    refresh();
  };

  return (
    <div className="max-w-4xl mx-auto">
      {tenantError && <ErrorBanner message={tenantError} />}
      {tenant && <TenantHeader tenant={tenant} />}
      {error && <ErrorBanner message={error} />}

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Campaigns</h2>
        <Link
          href={`/${tenantId}/campaigns/new`}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500"
        >
          + New Campaign
        </Link>
      </div>

      {loading && (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      )}

      <div className="flex flex-col gap-2">
        {!loading && campaigns.length === 0 && (
          <div className="text-slate-500 text-sm py-8 text-center">
            No campaigns yet.{" "}
            <Link href={`/${tenantId}/campaigns/new`} className="text-indigo-400 hover:underline">
              Create the first one.
            </Link>
          </div>
        )}
        {campaigns.map((c) => (
          <CampaignCard
            key={c.id}
            campaign={c}
            tenantId={tenantId}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  );
}
