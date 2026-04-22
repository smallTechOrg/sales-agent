"use client";

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
}

const sizeClass = {
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-10 w-10",
};

export function Spinner({ size = "md" }: SpinnerProps) {
  return (
    <div
      className={`${sizeClass[size]} animate-spin rounded-full border-2 border-slate-600 border-t-indigo-400`}
      role="status"
      aria-label="Loading"
    />
  );
}
