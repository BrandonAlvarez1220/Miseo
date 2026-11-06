import { cn } from "@/lib/utils";

/** Circular match indicator; color reflects how close the user is. */
export function MatchBadge({ value, className }: { value: number; className?: string }) {
  const tone = value >= 100 ? "text-primary" : value >= 70 ? "text-notice" : "text-accent";
  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  return (
    <div
      className={cn("relative size-14 shrink-0", tone, className)}
      role="img"
      aria-label={`${value}% de coincidencia`}
    >
      <svg viewBox="0 0 48 48" className="size-full -rotate-90">
        <circle
          cx="24"
          cy="24"
          r={radius}
          className="fill-none stroke-surface-muted"
          strokeWidth="5"
        />
        <circle
          cx="24"
          cy="24"
          r={radius}
          className="fill-none stroke-current"
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - value / 100)}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-ink">
        {value}%
      </span>
    </div>
  );
}
