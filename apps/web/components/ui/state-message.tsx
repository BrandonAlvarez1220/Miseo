import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface StateMessageProps {
  icon: LucideIcon;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  tone?: "neutral" | "danger";
  className?: string;
}

/** Shared layout for empty and error states. */
export function StateMessage({
  icon: Icon,
  title,
  description,
  action,
  tone = "neutral",
  className,
}: StateMessageProps) {
  return (
    <div
      role={tone === "danger" ? "alert" : "status"}
      className={cn(
        "flex flex-col items-center rounded-lg px-6 py-10 text-center",
        tone === "danger" ? "bg-danger-soft" : "bg-surface-muted",
        className,
      )}
    >
      <Icon
        aria-hidden="true"
        className={cn("mb-3 size-8", tone === "danger" ? "text-danger" : "text-ink-muted")}
      />
      <p className="text-lg font-semibold">{title}</p>
      {description ? <p className="mt-1 max-w-md text-sm text-ink-muted">{description}</p> : null}
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}
