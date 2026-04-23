"use client";

import { useEffect, useState } from "react";
import { api, type CompanyData } from "@/lib/api";

export function useCompanies(tenantId: string | null) {
  const [companies, setCompanies] = useState<CompanyData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId) return;
    setLoading(true);
    api
      .listCompanies(tenantId)
      .then((page) => setCompanies(page.items))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [tenantId]);

  return { companies, loading, error };
}