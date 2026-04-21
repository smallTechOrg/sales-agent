"use client";

import { useEffect, useState } from "react";
import { api, type OfferingData } from "@/lib/api";

export function useOfferings(tenantId: string | null) {
  const [offerings, setOfferings] = useState<OfferingData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId) return;
    setLoading(true);
    api
      .listOfferings(tenantId)
      .then((page) => setOfferings(page.items))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [tenantId]);

  return { offerings, loading, error };
}
