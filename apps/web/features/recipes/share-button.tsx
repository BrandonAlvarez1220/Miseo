"use client";

import { Check, Share2 } from "lucide-react";
import { useState } from "react";

import { buttonVariants } from "@/components/ui/button";

/** Uses the native share sheet when available; otherwise copies the link. */
export function ShareButton({ title }: { title: string }) {
  const [status, setStatus] = useState<"idle" | "copied" | "error">("idle");

  async function share() {
    const url = window.location.href;
    try {
      if (navigator.share) {
        await navigator.share({ title, url });
        return;
      }
      await navigator.clipboard.writeText(url);
      setStatus("copied");
      setTimeout(() => setStatus("idle"), 2000);
    } catch (error) {
      // The user closing the share sheet is not an error.
      if (error instanceof DOMException && error.name === "AbortError") return;
      console.error("Share failed", error);
      setStatus("error");
    }
  }

  return (
    <button type="button" onClick={share} className={buttonVariants({ variant: "secondary" })}>
      {status === "copied" ? <Check aria-hidden="true" /> : <Share2 aria-hidden="true" />}
      <span aria-live="polite">
        {status === "copied"
          ? "Enlace copiado"
          : status === "error"
            ? "No se pudo compartir"
            : "Compartir"}
      </span>
    </button>
  );
}
