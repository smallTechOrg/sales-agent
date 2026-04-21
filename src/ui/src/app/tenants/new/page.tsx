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
      // Credentials are optional and can be configured post-onboarding in Settings.
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

  const splitList = (s: string) =>
    s.split(",").map((v) => v.trim()).filter(Boolean);

  const handleSave = async () => {
    setSaving(true);
    setSaveError("");
    try {
      // 1. Create tenant
      const tenant = await api.createTenant(tenantName.trim());
      const tenantId = tenant.id;

      // 2. Create offering
      const offeringBody: Record<string, unknown> = {
        name: offering.name.trim(),
        value_proposition: offering.value_proposition.trim(),
        description: offering.icp_description.trim() || null,
        icp: {
          target_industries: splitList(offering.target_industries),
          target_roles: splitList(offering.target_roles),
          keywords: splitList(offering.keywords),
        },
      };
      const createdOffering = await api.createOffering(tenantId, offeringBody);
      const offeringId = createdOffering.id;

      // 3. Create campaign
      const campaignBody: Record<string, unknown> = {
        name: campaign.name.trim(),
        offering_id: offeringId,
        approval_mode: campaign.approval_mode,
        qualification_override: {
          threshold: campaign.qualification_threshold,
        },
        outreach_override: {
          channels: splitList(campaign.outreach_channels),
          follow_up_count: campaign.follow_up_count,
          follow_up_spacing_days: campaign.follow_up_spacing_days,
        },
      };
      await api.createCampaign(tenantId, campaignBody);

      // 4. Register tenant locally and navigate to its dashboard
      addKnownTenant(tenantId);
      setActiveTenant(tenantId);
      router.push(`/${tenantId}`);
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
          offerings={[]}
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
