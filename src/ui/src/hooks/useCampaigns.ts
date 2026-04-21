"use client";

import { useEffect, useState } from "react";
import { api, type CampaignData } from "@/lib/api";

export function useCampaigns(tenantId: string | null) {
  const [campaigns, setCampaigns] = useState<CampaignData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId) return;
    setLoading(true);
    api
      .listCampaigns(tenantId)
      .then((page) => setCampaigns(page.items))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [tenantId]);

  const refresh = () => {
    if (!tenantId) return;
    api
      .listCampaigns(tenantId)
      .then((page) => setCampaigns(page.items))
      .catch((e) => setError(String(e)));
  };

  return { campaigns, loading, error, refresh };
}
