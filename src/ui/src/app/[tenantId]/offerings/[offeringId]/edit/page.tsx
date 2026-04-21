"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { OfferingForm, OfferingState } from "@/components/forms/OfferingForm";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";

function toStr(arr: string[] | null | undefined): string {
  return arr ? arr.join(", ") : "";
}

function toList(s: string): string[] {
  return s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
}

export default function EditOfferingPage({
  params,
}: {
  params: Promise<{ tenantId: string; offeringId: string }>;
}) {
  const { tenantId, offeringId } = use(params);
  const router = useRouter();
  const [form, setForm] = useState<OfferingState | null>(null);
  const [errors, setErrors] = useState<Partial<Record<keyof OfferingState, string>>>({});
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .getOffering(tenantId, offeringId)
      .then((o) => {
        setForm({
          name: o.name,
          value_proposition: o.value_proposition ?? "",
          icp_description: o.description ?? "",
          target_industries: toStr((o.icp as Record<string, string[]> | null)?.target_industries),
          target_roles: toStr((o.icp as Record<string, string[]> | null)?.target_roles),
          keywords: toStr((o.icp as Record<string, string[]> | null)?.keywords),
        });
      })
      .catch((e) => setLoadError(e instanceof ApiError ? e.message : String(e)));
  }, [tenantId, offeringId]);

  function validate(): boolean {
    if (!form) return false;
    const e: typeof errors = {};
    if (!form.name.trim()) e.name = "Required";
    if (!form.value_proposition.trim()) e.value_proposition = "Required";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form || !validate()) return;
    setSaving(true);
    setSaveError("");
    try {
      await api.patchOffering(tenantId, offeringId, {
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

  if (loadError) return <ErrorBanner message={loadError} />;
  if (!form)
    return (
      <div className="flex justify-center py-8">
        <Spinner />
      </div>
    );

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Edit Offering</h1>
      {saveError && <ErrorBanner message={saveError} className="mb-4" />}
      <form onSubmit={handleSubmit} className="space-y-6">
        <OfferingForm value={form} onChange={setForm} errors={errors} />
        <button
          type="submit"
          disabled={saving}
          className="w-full py-2.5 rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-500 disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save changes"}
        </button>
      </form>
    </div>
  );
}
