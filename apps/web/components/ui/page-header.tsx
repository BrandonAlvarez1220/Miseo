import type { ReactNode } from "react";

import { Container } from "@/components/ui/container";

interface PageHeaderProps {
  /** First line, rendered light. */
  lead: string;
  /** Second line, rendered bold. */
  title: string;
  description?: ReactNode;
  /** Primary action(s) aligned to the right on large screens. */
  actions?: ReactNode;
  children?: ReactNode;
}

export function PageHeader({ lead, title, description, actions, children }: PageHeaderProps) {
  return (
    <Container className="pt-8 pb-6 sm:pt-10">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          <h1 className="text-3xl leading-tight tracking-tight text-balance sm:text-5xl">
            <span className="block font-light">{lead}</span>
            <span className="block font-bold">{title}</span>
          </h1>
          {description ? (
            <p className="mt-3 text-pretty text-ink-muted sm:text-lg">{description}</p>
          ) : null}
        </div>
        {actions ? <div className="flex shrink-0 flex-wrap gap-3">{actions}</div> : null}
      </div>
      {children}
    </Container>
  );
}
