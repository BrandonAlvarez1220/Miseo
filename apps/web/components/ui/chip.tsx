import { cva, type VariantProps } from "class-variance-authority";
import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export const chipVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full text-sm font-medium [&_svg]:size-3.5",
  {
    variants: {
      tone: {
        neutral: "bg-surface-muted text-ink",
        primary: "bg-primary-soft text-primary",
        accent: "bg-accent-soft text-accent",
      },
      size: {
        sm: "h-7 px-3 text-xs",
        md: "h-9 px-4",
      },
    },
    defaultVariants: { tone: "neutral", size: "md" },
  },
);

export type ChipProps = HTMLAttributes<HTMLSpanElement> & VariantProps<typeof chipVariants>;

/** Static label chip. Interactive ingredient chips build on these styles. */
export function Chip({ className, tone, size, ...props }: ChipProps) {
  return <span className={cn(chipVariants({ tone, size }), className)} {...props} />;
}
