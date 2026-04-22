"use client";

import { useEffect, useState } from "react";
import { api, type ApprovalItem } from "@/lib/api";

export function useApprovals(
  tenantId: string | null,
  params?: { campaign_id?: string; type?: string }
) {
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => {
    if (!tenantId) return;
    setLoading(true);
    api
      .listApprovals(tenantId, params)
      .then((page) => setApprovals(page.items))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId, params?.campaign_id, params?.type]);

  return { approvals, loading, error, refresh };
}
