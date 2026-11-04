import { CloudOff } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { StateMessage } from "@/components/ui/state-message";
import { ApiError } from "@/lib/api-client";

/**
 * Inline error for a failed API section. Re-throws non-API errors so genuine
 * bugs still reach the error boundary instead of being silently rendered.
 */
export function apiErrorState(error: unknown, retryHref: string, what: string) {
  if (!(error instanceof ApiError)) throw error;
  console.error(`Failed to load ${what}`, { code: error.code, status: error.status });
  return (
    <StateMessage
      tone="danger"
      icon={CloudOff}
      title={`No pudimos cargar ${what}`}
      description="El servicio no está disponible en este momento. Inténtalo de nuevo en unos segundos."
      action={
        <a href={retryHref} className={buttonVariants({ variant: "secondary", size: "sm" })}>
          Reintentar
        </a>
      }
    />
  );
}
