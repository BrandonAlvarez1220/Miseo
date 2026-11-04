"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { Container } from "@/components/ui/container";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <Container className="py-24 text-center">
      <h1 className="text-3xl font-bold">Algo salió mal</h1>
      <p className="mt-3 text-ink-muted">Ocurrió un error inesperado al mostrar esta página.</p>
      <Button className="mt-8" onClick={reset}>
        Intentar de nuevo
      </Button>
    </Container>
  );
}
