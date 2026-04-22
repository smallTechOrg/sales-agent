"use client";

interface SecretInputProps {
  id: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  hint?: string;
}

export function SecretInput({
  id,
  label,
  value,
  onChange,
  placeholder = "Enter secret…",
  hint,
}: SecretInputProps) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-slate-300">
        {label}
      </label>
      <input
        id={id}
        type="password"
        autoComplete="off"
        className="rounded bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
