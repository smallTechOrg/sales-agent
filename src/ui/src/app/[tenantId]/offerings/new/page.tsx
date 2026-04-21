"use client";

import { useState, use } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { OfferingForm, OfferingState, OFFERING_DEFAULTS } from "@/components/forms/OfferingForm";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { buildOfferingBody, validateOffering } from "@/lib/offering-utils";

export default function NewOfferingPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const router = useRouter();
  const [form, setForm] = useState<OfferingState>(OFFERING_DEFAULTS);
  const [errors, setErrors] = useState<Partial<Record<keyof OfferingState, string>>>({});
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validateOffering(form);
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }
    setErrors({});
    setSaving(true);
    setSaveError("");
    try {
      await api.createOffering(tenantId, buildOfferingBody(form));
      router.push(`/${tenantId}`);
    } catch (err) {
      setSaveError(err instanceof ApiError ? err.message : String(err));
      setSaving(false);
    }
  }

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">New Offering</h1>
      {saveError && <ErrorBanner message={saveError} className="mb-4" />}
      <form onSubmit={handleSubmit} className="space-y-6">
        <OfferingForm value={form} onChange={setForm} errors={errors} />
        <button
          type="submit"
          disabled={saving}
          className="w-full py-2.5 rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-500 disabled:opacity-50"
        >
          {saving ? "Creating…" : "Create offering"}
        </button>
      </form>
    </div>
  );
}
