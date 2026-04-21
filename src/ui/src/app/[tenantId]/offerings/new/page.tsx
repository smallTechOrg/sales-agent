"use client";

import { useState, use } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { OfferingForm, OfferingState } from "@/components/forms/OfferingForm";
import { ErrorBanner } from "@/components/ui/ErrorBanner";

const EMPTY: OfferingState = {
  name: "",
  value_proposition: "",
  icp_description: "",
  target_industries: "",
  target_roles: "",
  keywords: "",
};

function toList(s: string): string[] {
  return s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

export default function NewOfferingPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = use(params);
  const router = useRouter();
  const [form, setForm] = useState<OfferingState>(EMPTY);
  const [errors, setErrors] = useState<Partial<Record<keyof OfferingState, string>>>({});
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);

  function validate(): boolean {
    const e: typeof errors = {};
    if (!form.name.trim()) e.name = "Required";
    if (!form.value_proposition.trim()) e.value_proposition = "Required";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    setSaving(true);
    setSaveError("");
    try {
      await api.createOffering(tenantId, {
        name: form.name,
        value_proposition: form.value_proposition,
        description: form.icp_description || undefined,
        icp: {
          target_industries: toList(form.target_industries),
          target_roles: toList(form.target_roles),
          keywords: toList(form.keywords),
        },
      });
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
