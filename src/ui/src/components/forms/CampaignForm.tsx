"use client";

import type { OfferingData } from "@/lib/api";

export interface CampaignState {
  name: string;
  offering_id: string;
  approval_mode: "full_auto" | "approve_messages" | "approve_all";
  discovery_sources: string;
  qualification_threshold: number;
  outreach_channels: string;
  follow_up_count: number;
  follow_up_spacing_days: number;
}

interface CampaignFormProps {
  value: CampaignState;
  onChange: (v: CampaignState) => void;
  offerings: OfferingData[];
  errors?: Partial<Record<keyof CampaignState, string>>;
}

export function CampaignForm({
  value,
  onChange,
  offerings,
  errors,
}: CampaignFormProps) {
  const set =
    <K extends keyof CampaignState>(field: K) =>
    (v: CampaignState[K]) =>
      onChange({ ...value, [field]: v });

  const cls =
    "w-full rounded bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500";

  return (
    <div className="flex flex-col gap-5">
      <h2 className="text-lg font-bold text-white">Campaign</h2>

      {/* Name */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-300">
          Campaign name <span className="text-red-400">*</span>
        </label>
        <input
          type="text"
          className={cls}
          value={value.name}
          onChange={(e) => set("name")(e.target.value)}
        />
        {errors?.name && <p className="text-xs text-red-400">{errors.name}</p>}
      </div>

      {/* Offering */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-300">
          Offering <span className="text-red-400">*</span>
        </label>
        <select
          className={cls}
          value={value.offering_id}
          onChange={(e) => set("offering_id")(e.target.value)}
        >
          <option value="">— select offering —</option>
          {offerings.map((o) => (
            <option key={o.id} value={o.id}>
              {o.name}
            </option>
          ))}
        </select>
        {errors?.offering_id && (
          <p className="text-xs text-red-400">{errors.offering_id}</p>
        )}
      </div>

      {/* Approval mode */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-300">Approval mode</label>
        <select
          className={cls}
          value={value.approval_mode}
          onChange={(e) =>
            set("approval_mode")(
              e.target.value as CampaignState["approval_mode"]
            )
          }
        >
          <option value="full_auto">Full auto — send without review</option>
          <option value="approve_messages">Approve messages — review each draft</option>
          <option value="approve_all">Approve all — review leads + messages</option>
        </select>
      </div>

      {/* Discovery sources */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-300">Discovery sources</label>
        <input
          type="text"
          className={cls}
          placeholder="web, linkedin"
          value={value.discovery_sources}
          onChange={(e) => set("discovery_sources")(e.target.value)}
        />
        <p className="text-xs text-slate-500">Comma-separated.</p>
      </div>

      {/* Qualification threshold */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-300">
          Qualification score threshold: {value.qualification_threshold}
        </label>
        <input
          type="range"
          min={0}
          max={100}
          value={value.qualification_threshold}
          onChange={(e) => set("qualification_threshold")(Number(e.target.value))}
          className="accent-indigo-500"
        />
      </div>

      {/* Outreach channels */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-300">Outreach channels</label>
        <input
          type="text"
          className={cls}
          placeholder="email, whatsapp"
          value={value.outreach_channels}
          onChange={(e) => set("outreach_channels")(e.target.value)}
        />
        <p className="text-xs text-slate-500">Comma-separated.</p>
      </div>

      {/* Follow-up count */}
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-slate-300">Follow-up count</label>
          <input
            type="number"
            min={0}
            max={10}
            className={cls}
            value={value.follow_up_count}
            onChange={(e) => set("follow_up_count")(Number(e.target.value))}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-slate-300">Spacing (days)</label>
          <input
            type="number"
            min={1}
            max={30}
            className={cls}
            value={value.follow_up_spacing_days}
            onChange={(e) =>
              set("follow_up_spacing_days")(Number(e.target.value))
            }
          />
        </div>
      </div>
    </div>
  );
}
