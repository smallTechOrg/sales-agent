"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { OfferingForm, OfferingState } from "@/components/forms/OfferingForm";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Spinner } from "@/components/ui/Spinner";
import { buildOfferingBody, offeringRowToState, validateOffering } from "@/lib/offering-utils";

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
      .then((o) => setForm(offeringRowToState(o as unknown as Record<string, unknown>)))
      .catch((e) => setLoadError(e instanceof ApiError ? e.message : String(e)));
  }, [tenantId, offeringId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form) return;
    const errs = validateOffering(form);
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }
    setErrors({});
    setSaving(true);
    setSaveError("");
    try {
      await api.patchOffering(tenantId, offeringId, buildOfferingBody(form));
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
