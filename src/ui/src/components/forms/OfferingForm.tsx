"use client";

export interface OfferingState {
  name: string;
  value_proposition: string;
  icp_description: string;
  target_industries: string;
  target_roles: string;
  keywords: string;
}

interface OfferingFormProps {
  value: OfferingState;
  onChange: (v: OfferingState) => void;
  errors?: Partial<Record<keyof OfferingState, string>>;
}

function Field({
  id,
  label,
  value,
  onChange,
  error,
  multiline,
  hint,
  required,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  error?: string;
  multiline?: boolean;
  hint?: string;
  required?: boolean;
}) {
  const cls =
    "w-full rounded bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500";
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-slate-300">
        {label} {required && <span className="text-red-400">*</span>}
      </label>
      {multiline ? (
        <textarea
          id={id}
          rows={3}
          className={cls}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : (
        <input
          id={id}
          type="text"
          className={cls}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
      {error && <p className="text-xs text-red-400">{error}</p>}
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
        Define what this tenant sells and who it sells to.
      </p>
      <Field id="offering-name" label="Offering name" value={value.name} onChange={set("name")} error={errors?.name} required />
      <Field id="value-prop" label="Value proposition" value={value.value_proposition} onChange={set("value_proposition")} multiline error={errors?.value_proposition} required />
      <Field id="icp-desc" label="ICP description" value={value.icp_description} onChange={set("icp_description")} multiline hint="Describe the ideal customer in plain language." />
      <Field id="industries" label="Target industries" value={value.target_industries} onChange={set("target_industries")} hint="Comma-separated, e.g. SaaS, FinTech, Healthcare" />
      <Field id="roles" label="Target roles" value={value.target_roles} onChange={set("target_roles")} hint="Comma-separated, e.g. CEO, VP Sales, CTO" />
      <Field id="keywords" label="Keywords" value={value.keywords} onChange={set("keywords")} hint="Comma-separated discovery keywords." />
    </div>
  );
}
