"use client";

import { useEffect, useState } from "react";
import { api, type TenantData } from "@/lib/api";

export function useTenants() {
  const [tenants, setTenants] = useState<TenantData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .listTenants()
      .then(setTenants)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return { tenants, loading, error };
}
