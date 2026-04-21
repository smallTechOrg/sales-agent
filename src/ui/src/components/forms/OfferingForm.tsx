"use client";

export interface OfferingState {
  // Basics
  name: string;
  value_proposition: string;
  icp_description: string;
  // ICP
  target_industries: string;
  target_roles: string;
  keywords: string;
  negative_keywords: string;
  icp_geography: string;
  company_size_min: string;
  company_size_max: string;
  // Discovery
  discovery_sources: string;
  discovery_queries: string;
  discovery_geography: string;
  discovery_volume: string;
  // Qualification
  qualification_threshold: string;
  disqualifying_signals: string;
  // Outreach
  outreach_channels: string;
  outreach_tone: string;
  outreach_language: string;
  first_touch_template: string;
  follow_up_count: string;
  follow_up_spacing_days: string;
  send_schedule: string;
}

export const OFFERING_DEFAULTS: OfferingState = {
  name: "",
  value_proposition: "",
  icp_description: "",
  target_industries: "",
  target_roles: "",
  keywords: "",
  negative_keywords: "",
  icp_geography: "United States",
  company_size_min: "10",
  company_size_max: "500",
  discovery_sources: "web",
  discovery_queries: "{{role}} at {{industry}} company",
  discovery_geography: "United States",
  discovery_volume: "50",
  qualification_threshold: "60",
  disqualifying_signals: "",
  outreach_channels: "email",
  outreach_tone: "professional and friendly",
  outreach_language: "en",
  first_touch_template:
    "Hi {{name}},\n\nI came across {{company}} and thought you might benefit from {{offering}}.\n\n{{value_proposition}}\n\nWould you be open to a quick call?\n\nBest,\n{{sender_name}}",
  follow_up_count: "2",
  follow_up_spacing_days: "3",
  send_schedule: "09:00-17:00 Mon-Fri",
};

interface OfferingFormProps {
  value: OfferingState;
  onChange: (v: OfferingState) => void;
  errors?: Partial<Record<keyof OfferingState, string>>;
}

const inputCls =
  "w-full rounded bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500";

function Field({
  id,
  label,
  value,
  onChange,
  error,
  multiline,
  rows = 3,
  hint,
  required,
  placeholder,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  error?: string;
  multiline?: boolean;
  rows?: number;
  hint?: string;
  required?: boolean;
  placeholder?: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-slate-300">
        {label} {required && <span className="text-red-400">*</span>}
      </label>
      {multiline ? (
        <textarea
          id={id}
          rows={rows}
          className={inputCls}
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : (
        <input
          id={id}
          type="text"
          className={inputCls}
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}

function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="border-t border-slate-700 pt-5 mt-1">
      <h3 className="text-base font-semibold text-white">{title}</h3>
      {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
    </div>
  );
}

export function OfferingForm({ value, onChange, errors }: OfferingFormProps) {
  const set = (field: keyof OfferingState) => (v: string) =>
    onChange({ ...value, [field]: v });

  return (
    <div className="flex flex-col gap-5">
      <h2 className="text-lg font-bold text-white">Offering</h2>
      <p className="text-sm text-slate-400">
        Define what this tenant sells, who it sells to, and how the agent should run.
      </p>

      {/* Basics */}
      <Field id="offering-name" label="Offering name" value={value.name} onChange={set("name")} error={errors?.name} required />
      <Field id="value-prop" label="Value proposition" value={value.value_proposition} onChange={set("value_proposition")} multiline error={errors?.value_proposition} required hint="One or two sentences describing the core value delivered." />
      <Field id="icp-desc" label="ICP description (optional)" value={value.icp_description} onChange={set("icp_description")} multiline hint="Plain-language description of the ideal customer. Used as context for the AI." />

      {/* ICP */}
      <SectionHeader title="Ideal Customer Profile (ICP)" subtitle="Defines which companies and contacts the agent will target." />
      <Field id="industries" label="Target industries" value={value.target_industries} onChange={set("target_industries")} hint="Comma-separated. e.g. SaaS, FinTech, Healthcare" placeholder="SaaS, FinTech" />
      <Field id="roles" label="Target roles" value={value.target_roles} onChange={set("target_roles")} hint="Comma-separated. e.g. CEO, VP Sales, CTO" placeholder="CEO, VP Sales" />
      <Field id="keywords" label="Keywords" value={value.keywords} onChange={set("keywords")} hint="Comma-separated discovery keywords." placeholder="enterprise, B2B" />
      <Field id="neg-keywords" label="Negative keywords" value={value.negative_keywords} onChange={set("negative_keywords")} hint="Comma-separated. Leads matching these are excluded." placeholder="competitor, agency, freelance" />
      <Field id="icp-geo" label="Target geography" value={value.icp_geography} onChange={set("icp_geography")} hint="Comma-separated countries or regions." placeholder="United States, Canada" error={errors?.icp_geography} required />
      <div className="grid grid-cols-2 gap-4">
        <Field id="size-min" label="Company size min" value={value.company_size_min} onChange={set("company_size_min")} placeholder="10" error={errors?.company_size_min} required />
        <Field id="size-max" label="Company size max" value={value.company_size_max} onChange={set("company_size_max")} placeholder="500" error={errors?.company_size_max} required />
      </div>

      {/* Discovery */}
      <SectionHeader title="Discovery" subtitle="Controls how the agent finds leads each run." />
      <Field id="disc-sources" label="Discovery sources" value={value.discovery_sources} onChange={set("discovery_sources")} hint="Comma-separated: web, linkedin, directory" placeholder="web, linkedin" error={errors?.discovery_sources} required />
      <Field id="disc-queries" label="Query templates" value={value.discovery_queries} onChange={set("discovery_queries")} multiline rows={2} hint="One template per line. Use {{role}}, {{industry}}, {{geography}} as placeholders." placeholder={"{{role}} at {{industry}} company\n{{role}} {{industry}} {{geography}}"} error={errors?.discovery_queries} required />
      <Field id="disc-geo" label="Discovery geography" value={value.discovery_geography} onChange={set("discovery_geography")} hint="Comma-separated countries or regions to search." placeholder="United States, Canada" error={errors?.discovery_geography} required />
      <Field id="disc-vol" label="Volume per run" value={value.discovery_volume} onChange={set("discovery_volume")} hint="Max leads to discover per campaign run (1–1000)." placeholder="50" error={errors?.discovery_volume} required />

      {/* Qualification */}
      <SectionHeader title="Qualification" subtitle="How the agent decides which leads are worth contacting." />
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-300">
          Score threshold: {value.qualification_threshold}
          <span className="text-red-400"> *</span>
        </label>
        <input
          type="range"
          min={0}
          max={100}
          value={value.qualification_threshold}
          onChange={(e) => set("qualification_threshold")(e.target.value)}
          className="accent-indigo-500"
        />
        <p className="text-xs text-slate-500">Leads scoring below this are rejected (0–100).</p>
      </div>
      <Field id="disq-signals" label="Disqualifying signals" value={value.disqualifying_signals} onChange={set("disqualifying_signals")} hint="Comma-separated. Leads with these signals are auto-rejected." placeholder="no budget, out of market, student" />

      {/* Outreach */}
      <SectionHeader title="Outreach" subtitle="Controls how and when the agent contacts leads." />
      <Field id="out-channels" label="Channels" value={value.outreach_channels} onChange={set("outreach_channels")} hint="Comma-separated: email, whatsapp" placeholder="email" error={errors?.outreach_channels} required />
      <Field id="out-tone" label="Tone" value={value.outreach_tone} onChange={set("outreach_tone")} hint="Describe the tone for AI-generated messages." placeholder="professional and friendly" error={errors?.outreach_tone} required />
      <Field id="out-lang" label="Language" value={value.outreach_language} onChange={set("outreach_language")} hint="ISO 639-1 language code (e.g. en, es, fr)." placeholder="en" error={errors?.outreach_language} required />
      <Field id="first-touch" label="First touch template" value={value.first_touch_template} onChange={set("first_touch_template")} multiline rows={6} hint="Use {{name}}, {{company}}, {{offering}}, {{value_proposition}}, {{sender_name}} as placeholders." error={errors?.first_touch_template} required />
      <Field id="send-sched" label="Send schedule" value={value.send_schedule} onChange={set("send_schedule")} hint='When to send messages. e.g. "09:00-17:00 Mon-Fri"' placeholder="09:00-17:00 Mon-Fri" error={errors?.send_schedule} required />
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-slate-300">Follow-up count</label>
          <input
            type="number"
            min={0}
            max={10}
            className={inputCls}
            value={value.follow_up_count}
            onChange={(e) => set("follow_up_count")(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-slate-300">Spacing (days)</label>
          <input
            type="number"
            min={1}
            max={30}
            className={inputCls}
            value={value.follow_up_spacing_days}
            onChange={(e) => set("follow_up_spacing_days")(e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}
