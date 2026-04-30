import { AlertCircle, CheckCircle2, Info } from "lucide-react";
import type { ReactNode } from "react";

type StatusTone = "success" | "error" | "info";

type StatusMessageProps = {
  tone: StatusTone;
  children: ReactNode;
};

const toneStyles: Record<StatusTone, string> = {
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  error: "border-rose-200 bg-rose-50 text-rose-900",
  info: "border-stone-200 bg-stone-50 text-stone-800",
};

const icons = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

export function StatusMessage({ tone, children }: StatusMessageProps) {
  const Icon = icons[tone];

  return (
    <div
      className={`flex items-start gap-2 rounded-md border px-3 py-2 text-sm ${toneStyles[tone]}`}
    >
      <Icon aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0" />
      <div>{children}</div>
    </div>
  );
}
