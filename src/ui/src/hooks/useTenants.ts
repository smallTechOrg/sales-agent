"use client";

import { useEffect, useState } from "react";
import { api, type TenantData } from "@/lib/api";
import { useTenant } from "@/lib/tenant-context";

export function useTenants() {
  const { knownTenantIds } = useTenant();
  const [tenants, setTenants] = useState<(TenantData | null)[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (knownTenantIds.length === 0) {
      setTenants([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    Promise.all(
      knownTenantIds.map((id) =>
        api.getTenant(id).catch(() => null)
      )
    )
      .then(setTenants)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [knownTenantIds]);

  return { tenants, loading, error };
}
