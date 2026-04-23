// Typed API client — all endpoints.
// Every request automatically attaches X-Tenant-ID and Content-Type headers.

import { API_BASE } from "./constants";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  method: string,
  path: string,
  tenantId: string | null,
  body?: unknown
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (tenantId) headers["X-Tenant-ID"] = tenantId;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let code = "UNKNOWN";
    let message = res.statusText;
    try {
      const json = (await res.json()) as {
        error?: { code?: string; message?: string };
      };
      code = json.error?.code ?? code;
      message = json.error?.message ?? message;
    } catch {
      // non-JSON error body
    }
    throw new ApiError(res.status, code, message);
  }

  if (res.status === 204) return undefined as T;
  const json = (await res.json()) as { data: T };
  return json.data;
}

function get<T>(path: string, tenantId: string | null) {
  return request<T>("GET", path, tenantId);
}
function post<T>(path: string, tenantId: string | null, body: unknown) {
  return request<T>("POST", path, tenantId, body);
}
function patch<T>(path: string, tenantId: string | null, body: unknown) {
  return request<T>("PATCH", path, tenantId, body);
}
function del(path: string, tenantId: string | null) {
  return request<void>("DELETE", path, tenantId);
}

// ────────────────────────────────────────────────────────────────────────────
// Types
// ────────────────────────────────────────────────────────────────────────────

export interface HealthData {
  status: "ok" | "degraded";
}

export interface TenantData {
  id: string;
  name: string;
  default_approval_mode: string;
  retargeting_cooldown_days: number;
}

export interface OfferingData {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  value_proposition: string | null;
  pain_points: string[] | null;
  discovery_config: Record<string, unknown> | null;
  icp: Record<string, unknown> | null;
  qualification_config: Record<string, unknown> | null;
  outreach_config: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface CampaignData {
  id: string;
  tenant_id: string;
  offering_id: string;
  name: string;
  schedule: string | null;
  volume_cap: number | null;
  approval_mode: string | null;
  status: string;
  discovery_override: Record<string, unknown> | null;
  icp_override: Record<string, unknown> | null;
  qualification_override: Record<string, unknown> | null;
  outreach_override: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface LeadData {
  id: string;
  tenant_id: string;
  campaign_id: string;
  link_id: string | null;
  company_id: string | null;
  source: string | null;
  stage: string;
  company_name: string | null;
  domain: string | null;
  industry: string | null;
  headcount_range: string | null;
  business_type: string | null;
  research_summary: string | null;
  signals: string[] | null;
  score: number | null;
  per_criterion_scores: { criterion: string; score: number }[] | null;
  rationale: string | null;
  rejection_reason: string | null;
  detected_language: string | null;
  blocked_at: string | null;
  last_researched_at: string | null;
  created_at: string;
  updated_at: string;
}

// Alias
export type Lead = LeadData;

export interface LinkData {
  id: string;
  tenant_id: string;
  campaign_id: string;
  url: string;
  source: string;
  scrape_status: string;
  page_type: string | null;
  page_summary: string | null;
  page_detail: string | null;
  page_excerpt: string | null;
  scraped_at: string | null;
  identified_at: string | null;
  created_at: string;
}

export interface SourceLinkData {
  id: string;
  url: string;
  source: string;
  campaign_id: string | null;
  page_excerpt: string | null;
  scraped_at: string | null;
}

export interface CompanyData {
  id: string;
  tenant_id: string;
  domain: string;
  company_name: string | null;
  industry: string | null;
  headcount_range: string | null;
  business_type: string | null;
  research_summary: string | null;
  signals: string[] | null;
  notes: string | null;
  first_seen_at: string | null;
  last_enriched_at: string | null;
  source_links: SourceLinkData[];
  created_at: string;
  updated_at: string;
}

export interface MessageData {
  id: string;
  tenant_id: string;
  lead_id: string;
  campaign_id: string;
  channel: string;
  subject: string | null;
  body: string;
  sequence_number: number;
  status: string;
  sent_at: string | null;
  external_message_id: string | null;
  created_at: string;
}

// Alias
export type Message = MessageData;

export type ApprovalItem =
  | {
      type: "lead";
      id: string;
      campaign_id: string;
      stage: string;
      score: number | null;
      name: string | null;
      company: string | null;
      url: string;
      rationale: string | null;
    }
  | {
      type: "message";
      id: string;
      lead_id: string;
      channel: string;
      subject: string | null;
      body: string;
      sequence_number: number;
      personalisation_notes: string | null;
    };

// Alias
export type Approval = ApprovalItem;

export interface EventData {
  id: string;
  tenant_id: string;
  campaign_id: string | null;
  lead_id: string | null;
  event_type: string;
  payload: Record<string, unknown> | null;
  created_at: string;
}

// Alias
export type LeadEvent = EventData;

export interface ListPage<T> {
  items: T[];
  next_cursor: string | null;
}

export interface TriggerResult {
  run_id: string;
  message: string;
}

export interface RunData {
  id: string;
  campaign_id: string;
  tenant_id: string;
  status: "pending" | "running" | "completed" | "failed" | "interrupted";
  current_node: string | null;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  llm_call_count: number;
  estimated_cost_usd: number;
  created_at: string;
}

export interface RunEventSummary {
  run_id: string;
  counts: Record<string, number>;
}

export interface CampaignStats {
  campaign_id: string;
  total_links: number;
  total_leads: number;
  by_stage: Record<string, number>;
  messages_sent: number;
  replies_received: number;
}

export interface PersonSourceLink {
  id: string;
  url: string;
  source: string;
  page_excerpt: string | null;
  scraped_at: string | null;
}

export interface PersonData {
  id: string;
  tenant_id: string;
  lead_id: string;
  company_id: string | null;
  first_name: string | null;
  last_name: string | null;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  role: string | null;
  linkedin_url: string | null;
  approved_for_outreach: boolean;
  outreach_stopped: boolean;
  source_link: PersonSourceLink | null;
  created_at: string;
  updated_at: string;
}

export interface DecisionResult {
  decision: string;
}

// ────────────────────────────────────────────────────────────────────────────
// Endpoints
// ────────────────────────────────────────────────────────────────────────────

export const api = {
  health: () => get<HealthData>("/api/v1/health", null),

  // Tenants (creation — no tenant ID required)
  listTenants: () =>
    get<TenantData[]>("/api/v1/tenants", null),
  createTenant: (name: string) =>
    post<TenantData>("/api/v1/tenants", null, { name }),
  deleteTenant: (tenantId: string) =>
    del(`/api/v1/tenants/${tenantId}`, null),

  // Tenant (settings on an existing tenant)
  getTenant: (tenantId: string) =>
    get<TenantData>("/api/v1/tenant", tenantId),
  patchTenant: (tenantId: string, body: Partial<TenantData>) =>
    patch<TenantData>("/api/v1/tenant", tenantId, body),

  // Offerings
  listOfferings: (tenantId: string, cursor?: string) =>
    get<ListPage<OfferingData>>(
      `/api/v1/offerings${cursor ? `?cursor=${cursor}` : ""}`,
      tenantId
    ),
  getOffering: (tenantId: string, id: string) =>
    get<OfferingData>(`/api/v1/offerings/${id}`, tenantId),
  createOffering: (tenantId: string, body: Record<string, unknown>) =>
    post<OfferingData>("/api/v1/offerings", tenantId, body),
  patchOffering: (
    tenantId: string,
    id: string,
    body: Record<string, unknown>
  ) => patch<OfferingData>(`/api/v1/offerings/${id}`, tenantId, body),
  deleteOffering: (tenantId: string, id: string) =>
    del(`/api/v1/offerings/${id}`, tenantId),

  // Campaigns
  listCampaigns: (tenantId: string, cursor?: string) =>
    get<ListPage<CampaignData>>(
      `/api/v1/campaigns${cursor ? `?cursor=${cursor}` : ""}`,
      tenantId
    ),
  getCampaign: (tenantId: string, id: string) =>
    get<CampaignData>(`/api/v1/campaigns/${id}`, tenantId),
  createCampaign: (tenantId: string, body: Record<string, unknown>) =>
    post<CampaignData>("/api/v1/campaigns", tenantId, body),
  patchCampaign: (
    tenantId: string,
    id: string,
    body: Record<string, unknown>
  ) => patch<CampaignData>(`/api/v1/campaigns/${id}`, tenantId, body),
  deleteCampaign: (tenantId: string, id: string) =>
    del(`/api/v1/campaigns/${id}`, tenantId),
  triggerCampaign: (tenantId: string, id: string) =>
    post<TriggerResult>(`/api/v1/campaigns/${id}/trigger`, tenantId, {}),
  listRuns: (tenantId: string, campaignId: string, cursor?: string) =>
    get<ListPage<RunData>>(
      `/api/v1/campaigns/${campaignId}/runs${cursor ? `?cursor=${cursor}` : ""}`,
      tenantId
    ),
  getRun: (tenantId: string, campaignId: string, runId: string) =>
    get<RunData>(`/api/v1/campaigns/${campaignId}/runs/${runId}`, tenantId),
  getRunEventSummary: (tenantId: string, campaignId: string, runId: string) =>
    get<RunEventSummary>(`/api/v1/campaigns/${campaignId}/runs/${runId}/events/summary`, tenantId),
  getCampaignStats: (tenantId: string, campaignId: string) =>
    get<CampaignStats>(`/api/v1/campaigns/${campaignId}/stats`, tenantId),

  // Leads
  listLeads: (
    tenantId: string,
    params: {
      campaign_id?: string;
      stage?: string;
      cursor?: string;
      limit?: number;
    }
  ) => {
    const q = new URLSearchParams();
    if (params.campaign_id) q.set("campaign_id", params.campaign_id);
    if (params.stage) q.set("stage", params.stage);
    if (params.cursor) q.set("cursor", params.cursor);
    if (params.limit) q.set("limit", String(params.limit));
    return get<ListPage<LeadData>>(
      `/api/v1/leads${q.toString() ? `?${q}` : ""}`,
      tenantId
    );
  },
  getLead: (tenantId: string, id: string) =>
    get<LeadData>(`/api/v1/leads/${id}`, tenantId),
  patchLead: (tenantId: string, id: string, body: Record<string, unknown>) =>
    patch<LeadData>(`/api/v1/leads/${id}`, tenantId, body),

  // Links
  getLink: (tenantId: string, linkId: string) =>
    get<LinkData>(`/api/v1/links/${linkId}`, tenantId),
  listLinks: (tenantId: string, campaignId?: string, cursor?: string) => {
    const q = new URLSearchParams();
    if (campaignId) q.set("campaign_id", campaignId);
    if (cursor) q.set("cursor", cursor);
    return get<ListPage<LinkData>>(`/api/v1/links${q.toString() ? `?${q}` : ""}`, tenantId);
  },

  // Companies
  listCompanies: (tenantId: string, cursor?: string) =>
    get<ListPage<CompanyData>>(
      `/api/v1/companies${cursor ? `?cursor=${cursor}` : ""}`,
      tenantId
    ),
  getCompany: (tenantId: string, id: string) =>
    get<CompanyData>(`/api/v1/companies/${id}`, tenantId),
  patchCompany: (tenantId: string, id: string, body: Partial<CompanyData>) =>
    patch<CompanyData>(`/api/v1/companies/${id}`, tenantId, body),

  // People
  listPeople: (
    tenantId: string,
    params?: { company_id?: string; cursor?: string }
  ) => {
    const q = new URLSearchParams();
    if (params?.company_id) q.set("company_id", params.company_id);
    if (params?.cursor) q.set("cursor", params.cursor);
    return get<ListPage<PersonData>>(
      `/api/v1/people${q.toString() ? `?${q}` : ""}`,
      tenantId
    );
  },
  getPerson: (tenantId: string, id: string) =>
    get<PersonData>(`/api/v1/people/${id}`, tenantId),
  patchPerson: (tenantId: string, id: string, body: { approved_for_outreach?: boolean; outreach_stopped?: boolean }) =>
    patch<PersonData>(`/api/v1/people/${id}`, tenantId, body),

  // Approvals
  listApprovals: (
    tenantId: string,
    params?: { campaign_id?: string; type?: string; cursor?: string }
  ) => {
    const q = new URLSearchParams();
    if (params?.campaign_id) q.set("campaign_id", params.campaign_id);
    if (params?.type) q.set("type", params.type);
    if (params?.cursor) q.set("cursor", params.cursor);
    return get<ListPage<ApprovalItem>>(
      `/api/v1/approvals${q.toString() ? `?${q}` : ""}`,
      tenantId
    );
  },
  qualifyLead: (
    tenantId: string,
    leadId: string,
    decision: "approve" | "reject",
    reason?: string
  ) =>
    post<DecisionResult>(
      `/api/v1/approvals/leads/${leadId}/qualify`,
      tenantId,
      { decision, ...(reason ? { reason } : {}) }
    ),
  approveMessage: (
    tenantId: string,
    messageId: string,
    payload: { decision: "approve" | "reject"; body?: string; reason?: string }
  ) =>
    post<DecisionResult>(
      `/api/v1/approvals/messages/${messageId}`,
      tenantId,
      payload
    ),

  // Messages
  listMessages: (
    tenantId: string,
    params?: {
      campaign_id?: string;
      lead_id?: string;
      status?: string;
      cursor?: string;
    }
  ) => {
    const q = new URLSearchParams();
    if (params?.campaign_id) q.set("campaign_id", params.campaign_id);
    if (params?.lead_id) q.set("lead_id", params.lead_id);
    if (params?.status) q.set("status", params.status);
    if (params?.cursor) q.set("cursor", params.cursor);
    return get<ListPage<MessageData>>(
      `/api/v1/messages${q.toString() ? `?${q}` : ""}`,
      tenantId
    );
  },
  getMessage: (tenantId: string, id: string) =>
    get<MessageData>(`/api/v1/messages/${id}`, tenantId),

  // Events
  listEvents: (
    tenantId: string,
    params?: {
      campaign_id?: string;
      lead_id?: string;
      event_type?: string;
      from?: string;
      cursor?: string;
      limit?: number;
    }
  ) => {
    const q = new URLSearchParams();
    if (params?.campaign_id) q.set("campaign_id", params.campaign_id);
    if (params?.lead_id) q.set("lead_id", params.lead_id);
    if (params?.event_type) q.set("event_type", params.event_type);
    if (params?.from) q.set("from", params.from);
    if (params?.cursor) q.set("cursor", params.cursor);
    if (params?.limit) q.set("limit", String(params.limit));
    return get<ListPage<EventData>>(
      `/api/v1/events${q.toString() ? `?${q}` : ""}`,
      tenantId
    );
  },
};
