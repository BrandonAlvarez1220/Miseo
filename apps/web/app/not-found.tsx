import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { Container } from "@/components/ui/container";

export default function NotFound() {
  return (
    <Container className="py-24 text-center">
      <p className="text-xs font-semibold tracking-[0.18em] text-primary uppercase">Error 404</p>
      <h1 className="mt-3 text-4xl font-bold">Esta página no está en el menú</h1>
      <p className="mt-3 text-ink-muted">
        Puede que el enlace sea antiguo o que la receta se haya movido.
      </p>
      <Link href="/" className={`${buttonVariants()} mt-8`}>
        Volver al inicio
      </Link>
    </Container>
  );
}
