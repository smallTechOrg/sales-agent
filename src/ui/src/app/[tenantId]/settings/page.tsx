"use client";

import { useEffect, useState, use } from "react";
import { api, type TenantData, ApiError } from "@/lib/api";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";

function Field({
  id,
  label,
  hint,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-slate-300">
        {label}
      </label>
      {children}
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

const inputCls =
  "rounded-lg bg-slate-900 border border-slate-700 text-white text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent";

export default function SettingsPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const [tenant, setTenant] = useState<TenantData | null>(null);
  const [form, setForm] = useState({
    name: "",
    default_approval_mode: "full_auto",
    retargeting_cooldown_days: 30,
  });
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api
      .getTenant(tenantId)
      .then((t) => {
        setTenant(t);
        setForm({
          name: t.name,
          default_approval_mode: t.default_approval_mode,
          retargeting_cooldown_days: t.retargeting_cooldown_days,
        });
      })
      .catch((e) => setLoadError(e instanceof ApiError ? e.message : String(e)));
  }, [tenantId]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaveError("");
    setSaved(false);
    setSaving(true);
    try {
      const updated = await api.patchTenant(tenantId, {
        name: form.name,
        default_approval_mode: form.default_approval_mode,
        retargeting_cooldown_days: form.retargeting_cooldown_days,
      });
      setTenant(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      setSaveError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  if (loadError) return <ErrorBanner message={loadError} />;
  if (!tenant)
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-bold text-white mb-2">Settings</h1>
      <p className="text-sm text-slate-500 mb-8 font-mono">{tenantId}</p>

      {saveError && <ErrorBanner message={saveError} className="mb-4" />}

      <form onSubmit={handleSave} className="space-y-6">
        <section className="bg-slate-800 rounded-xl border border-slate-700 p-5 space-y-5">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
            General
          </h2>

          <Field id="name" label="Tenant name">
            <input
              id="name"
              type="text"
              className={inputCls}
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </Field>

          <Field
            id="approval-mode"
            label="Default approval mode"
            hint="Applied to new campaigns unless overridden."
          >
            <select
              id="approval-mode"
              className={inputCls}
              value={form.default_approval_mode}
              onChange={(e) =>
                setForm({ ...form, default_approval_mode: e.target.value })
              }
            >
              <option value="full_auto">Full auto — send without review</option>
              <option value="approve_messages">
                Approve messages — review each draft
              </option>
              <option value="approve_all">
                Approve all — review leads + messages
              </option>
            </select>
          </Field>

          <Field
            id="cooldown"
            label="Retargeting cooldown (days)"
            hint="Minimum days before re-contacting a lead."
          >
            <input
              id="cooldown"
              type="number"
              min={0}
              max={365}
              className={inputCls + " w-32"}
              value={form.retargeting_cooldown_days}
              onChange={(e) =>
                setForm({
                  ...form,
                  retargeting_cooldown_days: Number(e.target.value),
                })
              }
            />
          </Field>
        </section>

        <div className="flex items-center gap-4">
          <button
            type="submit"
            disabled={saving}
            className="px-5 py-2 rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-500 disabled:opacity-50 flex items-center gap-2"
          >
            {saving && <Spinner size="sm" />}
            Save changes
          </button>
          {saved && (
            <span className="text-sm text-emerald-400">Saved successfully.</span>
          )}
        </div>
      </form>
    </div>
  );
}
