"use client";

import { useEffect, useState } from "react";
import { api, type CustomerData } from "@/lib/api";

export function useCustomers(tenantId: string | null) {
  const [customers, setCustomers] = useState<CustomerData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId) return;
    setLoading(true);
    api
      .listCustomers(tenantId)
      .then((page) => setCustomers(page.items))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [tenantId]);

  return { customers, loading, error };
}
