import type { OfferingState, RubricCriterion } from "@/components/forms/OfferingForm";

function toList(s: string): string[] {
  return s.split(",").map((x) => x.trim()).filter(Boolean);
}

function toLines(s: string): string[] {
  return s.split("\n").map((x) => x.trim()).filter(Boolean);
}

export function validateOffering(
  form: OfferingState
): Partial<Record<keyof OfferingState, string>> {
  const e: Partial<Record<keyof OfferingState, string>> = {};
  if (!form.name.trim()) e.name = "Required";
  if (!form.value_proposition.trim()) e.value_proposition = "Required";
  if (!form.icp_geography.trim()) e.icp_geography = "Required";
  if (!form.company_size_min || isNaN(Number(form.company_size_min))) e.company_size_min = "Must be a number";
  if (!form.company_size_max || isNaN(Number(form.company_size_max))) e.company_size_max = "Must be a number";
  if (!form.discovery_sources.trim()) e.discovery_sources = "Required";
  if (!form.discovery_queries.trim()) e.discovery_queries = "Required";
  if (!form.discovery_geography.trim()) e.discovery_geography = "Required";
  if (!form.discovery_volume || isNaN(Number(form.discovery_volume))) e.discovery_volume = "Must be a number";
  if (!form.outreach_channels.trim()) e.outreach_channels = "Required";
  if (!form.outreach_tone.trim()) e.outreach_tone = "Required";
  if (!form.outreach_language.trim()) e.outreach_language = "Required";
  if (!form.first_touch_template.trim()) e.first_touch_template = "Required";
  if (!form.send_schedule.trim()) e.send_schedule = "Required";
  if (form.rubric_criteria.filter((c) => c.name.trim()).length === 0)
    e.name = "At least one qualification criterion is required";
  return e;
}

export function buildOfferingBody(form: OfferingState): Record<string, unknown> {
  const threshold = Number(form.qualification_threshold) || 60;
  return {
    name: form.name.trim(),
    value_proposition: form.value_proposition.trim(),
    description: form.icp_description.trim() || null,
    pain_points: [],
    icp: {
      target_industries: toList(form.target_industries),
      target_roles: toList(form.target_roles),
      keywords: toList(form.keywords),
      negative_keywords: toList(form.negative_keywords),
      geography: toList(form.icp_geography),
      company_size_range: {
        min: Number(form.company_size_min) || 1,
        max: Number(form.company_size_max) || 1000,
      },
    },
    discovery_config: {
      sources: toList(form.discovery_sources),
      query_templates: toLines(form.discovery_queries),
      geography: toList(form.discovery_geography),
      volume_per_run: Number(form.discovery_volume) || 50,
    },
    qualification_config: {
      rubric_criteria: form.rubric_criteria
        .filter((c) => c.name.trim())
        .map((c) => ({
          name: c.name.trim(),
          description: c.description.trim() || c.name.trim(),
          weight: Math.max(0.01, Math.min(1.0, Number(c.weight) || 0.1)),
        })),
      score_threshold: threshold,
      disqualifying_signals: toList(form.disqualifying_signals),
    },
    outreach_config: {
      channels_enabled: toList(form.outreach_channels),
      tone: form.outreach_tone.trim(),
      language_default: form.outreach_language.trim(),
      templates: {
        first_touch: form.first_touch_template.trim(),
      },
      follow_up_count: Number(form.follow_up_count) || 0,
      follow_up_spacing_days: Number(form.follow_up_spacing_days) || 3,
      send_schedule: form.send_schedule.trim(),
    },
  };
}

export function offeringRowToState(o: Record<string, unknown>): OfferingState {
  const icp = (o.icp as Record<string, unknown> | null) ?? {};
  const disc = (o.discovery_config as Record<string, unknown> | null) ?? {};
  const qual = (o.qualification_config as Record<string, unknown> | null) ?? {};
  const out = (o.outreach_config as Record<string, unknown> | null) ?? {};
  const tpls = (out.templates as Record<string, string> | null) ?? {};
  const sizeRange = (icp.company_size_range as { min?: number; max?: number } | null) ?? {};

  const rawCriteria = (qual.rubric_criteria as Array<Record<string, unknown>> | null) ?? [];
  const rubric_criteria: RubricCriterion[] = rawCriteria.map((c) => ({
    name: String(c.name ?? ""),
    description: String(c.description ?? ""),
    weight: String(c.weight ?? "0.1"),
  }));

  return {
    name: String(o.name ?? ""),
    value_proposition: String(o.value_proposition ?? ""),
    icp_description: String(o.description ?? ""),
    target_industries: ((icp.target_industries as string[]) ?? []).join(", "),
    target_roles: ((icp.target_roles as string[]) ?? []).join(", "),
    keywords: ((icp.keywords as string[]) ?? []).join(", "),
    negative_keywords: ((icp.negative_keywords as string[]) ?? []).join(", "),
    icp_geography: ((icp.geography as string[]) ?? []).join(", "),
    company_size_min: String(sizeRange.min ?? 10),
    company_size_max: String(sizeRange.max ?? 500),
    discovery_sources: ((disc.sources as string[]) ?? []).join(", "),
    discovery_queries: ((disc.query_templates as string[]) ?? []).join("\n"),
    discovery_geography: ((disc.geography as string[]) ?? []).join(", "),
    discovery_volume: String(disc.volume_per_run ?? 50),
    rubric_criteria: rubric_criteria.length > 0
      ? rubric_criteria
      : [{ name: "Overall fit", description: "Matches the ideal customer profile", weight: "1.0" }],
    qualification_threshold: String(qual.score_threshold ?? 60),
    disqualifying_signals: ((qual.disqualifying_signals as string[]) ?? []).join(", "),
    outreach_channels: ((out.channels_enabled as string[]) ?? []).join(", "),
    outreach_tone: String(out.tone ?? "professional and friendly"),
    outreach_language: String(out.language_default ?? "en"),
    first_touch_template: String(tpls.first_touch ?? ""),
    follow_up_count: String(out.follow_up_count ?? 2),
    follow_up_spacing_days: String(out.follow_up_spacing_days ?? 3),
    send_schedule: String(out.send_schedule ?? "09:00-17:00 Mon-Fri"),
  };
}
