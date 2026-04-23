"use client";

import { useEffect, useState } from "react";
import { api, type PersonData } from "@/lib/api";

export function usePeople(
  tenantId: string | null,
  params?: { company_id?: string }
) {
  const [people, setPeople] = useState<PersonData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const companyId = params?.company_id;

  useEffect(() => {
    if (!tenantId) return;
    setLoading(true);
    api
      .listPeople(tenantId, { company_id: companyId })
      .then((page) => setPeople(page.items))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [tenantId, companyId]);

  return { people, loading, error };
}