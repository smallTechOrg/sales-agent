"use client";

import { useEffect, useState } from "react";
import { api, type MessageData } from "@/lib/api";

interface UseMessagesParams {
  tenantId: string | null;
  campaignId?: string;
  leadId?: string;
  status?: string;
}

export function useMessages({
  tenantId,
  campaignId,
  leadId,
  status,
}: UseMessagesParams) {
  const [messages, setMessages] = useState<MessageData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId) return;
    setLoading(true);
    api
      .listMessages(tenantId, { campaign_id: campaignId, lead_id: leadId, status })
      .then((page) => setMessages(page.items))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [tenantId, campaignId, leadId, status]);

  return { messages, loading, error };
}
