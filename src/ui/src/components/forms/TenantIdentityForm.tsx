"use client";

interface TenantIdentityFormProps {
  name: string;
  onChange: (name: string) => void;
  error?: string;
}

export function TenantIdentityForm({
  name,
  onChange,
  error,
}: TenantIdentityFormProps) {
  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-bold text-white">Tenant Identity</h2>
      <p className="text-sm text-slate-400">
        Give this tenant a display name. A UUID will be generated automatically.
      </p>
      <div className="flex flex-col gap-1">
        <label htmlFor="tenant-name" className="text-sm font-medium text-slate-300">
          Display name <span className="text-red-400">*</span>
        </label>
        <input
          id="tenant-name"
          type="text"
          className="rounded bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500"
          placeholder="Acme Corp"
          value={name}
          onChange={(e) => onChange(e.target.value)}
        />
        {error && <p className="text-xs text-red-400">{error}</p>}
      </div>
    </div>
  );
}
