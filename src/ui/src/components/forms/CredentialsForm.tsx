"use client";

import { SecretInput } from "@/components/ui/SecretInput";

export interface CredentialsState {
  gmail_token: string;
  whatsapp_key: string;
  slack_webhook: string;
}

interface CredentialsFormProps {
  value: CredentialsState;
  onChange: (v: CredentialsState) => void;
}

export function CredentialsForm({ value, onChange }: CredentialsFormProps) {
  const set = (field: keyof CredentialsState) => (v: string) =>
    onChange({ ...value, [field]: v });

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-lg font-bold text-white">Credentials</h2>
      <p className="text-sm text-slate-400">
        All credentials are encrypted at rest with Fernet. They are never returned by
        the API after saving.
      </p>

      <SecretInput
        id="gmail-token"
        label="Gmail OAuth token (JSON blob)"
        value={value.gmail_token}
        onChange={set("gmail_token")}
        placeholder='{"token": "ya29...", "refresh_token": "..."}'
        hint="Paste the full OAuth2 credentials JSON from Google."
      />

      <SecretInput
        id="whatsapp-key"
        label="WhatsApp API key"
        value={value.whatsapp_key}
        onChange={set("whatsapp_key")}
        placeholder="EAAxxxxx…"
        hint="Your WhatsApp Cloud API bearer token."
      />

      <SecretInput
        id="slack-webhook"
        label="Slack webhook URL (optional)"
        value={value.slack_webhook}
        onChange={set("slack_webhook")}
        placeholder="https://hooks.slack.com/services/…"
        hint="Optional. Used for approval notifications."
      />
    </div>
  );
}
