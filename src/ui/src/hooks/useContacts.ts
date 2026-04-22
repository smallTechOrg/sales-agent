"use client";

import { useEffect, useState } from "react";
import { api, type ContactData } from "@/lib/api";

export function useContacts(
  tenantId: string | null,
  params?: { customer_id?: string }
) {
  const [contacts, setContacts] = useState<ContactData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const customerId = params?.customer_id;

  useEffect(() => {
    if (!tenantId) return;
    setLoading(true);
    api
      .listContacts(tenantId, { customer_id: customerId })
      .then((page) => setContacts(page.items))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [tenantId, customerId]);

  return { contacts, loading, error };
}
