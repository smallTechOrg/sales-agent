"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { StepIndicator } from "@/components/ui/StepIndicator";
import { TenantIdentityForm } from "@/components/forms/TenantIdentityForm";
import {
  CredentialsForm,
  type CredentialsState,
} from "@/components/forms/CredentialsForm";
import { OfferingForm, type OfferingState } from "@/components/forms/OfferingForm";
import { CampaignForm, type CampaignState } from "@/components/forms/CampaignForm";
import { WizardReview } from "@/components/forms/WizardReview";
import { useTenant } from "@/lib/tenant-context";
import { api } from "@/lib/api";

const EMPTY_OFFERING: OfferingState = {
  name: "",
  value_proposition: "",
  icp_description: "",
  target_industries: "",
  target_roles: "",
  keywords: "",
};

const EMPTY_CAMPAIGN: CampaignState = {
  name: "",
  offering_id: "",
  approval_mode: "full_auto",
  discovery_sources: "web",
  qualification_threshold: 60,
  outreach_channels: "email",
  follow_up_count: 2,
  follow_up_spacing_days: 3,
};

const EMPTY_CREDS: CredentialsState = {
  gmail_token: "",
  whatsapp_key: "",
  slack_webhook: "",
};

export default function NewTenantPage() {
  const router = useRouter();
  const { addKnownTenant, setActiveTenant } = useTenant();

  const [step, setStep] = useState(0);
  const [tenantName, setTenantName] = useState("");
  const [nameError, setNameError] = useState("");
  const [credentials, setCredentials] = useState<CredentialsState>(EMPTY_CREDS);
  const [offering, setOffering] = useState<OfferingState>(EMPTY_OFFERING);
  const [offeringErrors, setOfferingErrors] = useState<
    Partial<Record<keyof OfferingState, string>>
  >({});
  const [campaign, setCampaign] = useState<CampaignState>(EMPTY_CAMPAIGN);
  const [campaignErrors, setCampaignErrors] = useState<
    Partial<Record<keyof CampaignState, string>>
  >({});
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);
  // Saved offering ID after the API call in step 2→3
  const [savedOfferingId, setSavedOfferingId] = useState<string | null>(null);

  const next = async () => {
    if (step === 0) {
      if (!tenantName.trim()) {
        setNameError("Display name is required.");
        return;
      }
      setNameError("");
      setStep(1);
      return;
    }

    if (step === 1) {
      // NOTE: POST /api/v1/tenants does not exist yet.
      // For now, skip straight to offering creation with a warning.
      setStep(2);
      return;
    }

    if (step === 2) {
      const errs: Partial<Record<keyof OfferingState, string>> = {};
      if (!offering.name.trim()) errs.name = "Required.";
      if (!offering.value_proposition.trim())
        errs.value_proposition = "Required.";
      if (Object.keys(errs).length) {
        setOfferingErrors(errs);
        return;
      }
      setOfferingErrors({});
      setStep(3);
      return;
    }

    if (step === 3) {
      const errs: Partial<Record<keyof CampaignState, string>> = {};
      if (!campaign.name.trim()) errs.name = "Required.";
      if (Object.keys(errs).length) {
        setCampaignErrors(errs);
        return;
      }
      setCampaignErrors({});
      setStep(4);
      return;
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError("");
    try {
      // POST /api/v1/tenants — NOT YET IMPLEMENTED ON BACKEND
      // Show a clear message to the user.
      throw new Error(
        "POST /api/v1/tenants is not yet implemented. " +
          "Create the tenant via the CLI (`zer0 tenant add`) and then use " +
          "the Dashboard home to add its UUID."
      );
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">New Tenant</h1>
      <StepIndicator current={step} />

      {step === 0 && (
        <TenantIdentityForm
          name={tenantName}
          onChange={setTenantName}
          error={nameError}
        />
      )}
      {step === 1 && (
        <CredentialsForm value={credentials} onChange={setCredentials} />
      )}
      {step === 2 && (
        <OfferingForm
          value={offering}
          onChange={setOffering}
          errors={offeringErrors}
        />
      )}
      {step === 3 && (
        <CampaignForm
          value={campaign}
          onChange={setCampaign}
          offerings={
            savedOfferingId
              ? [
                  {
                    id: savedOfferingId,
                    tenant_id: "",
                    name: offering.name,
                    value_proposition: offering.value_proposition,
                    description: offering.icp_description || null,
                    pain_points: null,
                    icp: {
                      target_industries: offering.target_industries.split(",").map((s) => s.trim()),
                      target_roles: offering.target_roles.split(",").map((s) => s.trim()),
                      keywords: offering.keywords.split(",").map((s) => s.trim()),
                    },
                    discovery_config: null,
                    qualification_config: null,
                    outreach_config: null,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                  },
                ]
              : []
          }
          errors={campaignErrors}
        />
      )}
      {step === 4 && (
        <WizardReview
          tenantName={tenantName}
          credentials={credentials}
          offering={offering}
          campaign={campaign}
          onEdit={setStep}
          onSave={handleSave}
          saving={saving}
          error={saveError}
        />
      )}

      {step < 4 && (
        <div className="flex gap-3 mt-8">
          {step > 0 && (
            <button
              onClick={() => setStep(step - 1)}
              className="rounded-md bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-600"
            >
              Back
            </button>
          )}
          <button
            onClick={next}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
