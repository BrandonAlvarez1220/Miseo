import { FlaskConical } from "lucide-react";
import type { Metadata } from "next";
import { Suspense } from "react";

import { Container } from "@/components/ui/container";
import { loginAction } from "@/features/auth/actions";
import { getSession } from "@/features/auth/current-user";
import { SubmitButton } from "@/features/auth/submit-button";
import { safeRedirectPath } from "@/lib/safe-redirect";

export const metadata: Metadata = { title: "Ingresar" };

const ERRORS: Record<string, string> = {
  disabled:
    "El ingreso local no está habilitado en este servidor (DEV_LOGIN_ENABLED). En producción se usará Supabase.",
  email: "Escribe un correo válido (no uses dominios reservados como .local o .test).",
  unavailable: "No pudimos conectar con el servidor. Inténtalo de nuevo en unos segundos.",
};

export default function LoginPage({ searchParams }: PageProps<"/ingresar">) {
  return (
    <Container className="py-12 sm:py-20">
      <Suspense fallback={null}>
        <LoginCard searchParams={searchParams} />
      </Suspense>
    </Container>
  );
}

async function LoginCard({ searchParams }: Pick<PageProps<"/ingresar">, "searchParams">) {
  const params = await searchParams;
  const first = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value);
  const next = safeRedirectPath(first(params.next));
  const error = ERRORS[first(params.error) ?? ""];
  const session = await getSession();

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-3xl font-bold tracking-tight">Ingresar</h1>
      <p className="mt-2 text-ink-muted">
        {session
          ? `Ya iniciaste sesión como ${session.user.display_name}.`
          : "Entra para guardar tu progreso y, si eres moderador, revisar recetas."}
      </p>

      <p className="mt-6 flex items-start gap-2 rounded-md bg-notice-soft px-4 py-3 text-sm">
        <FlaskConical aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-notice" />
        <span>
          <strong>Modo de desarrollo local.</strong> No hay contraseña: escribe cualquier correo y
          entrarás con él. Al publicar, esto se reemplaza por Supabase.
        </span>
      </p>

      {error ? (
        <p role="alert" className="mt-4 rounded-md bg-danger-soft px-4 py-3 text-sm text-danger">
          {error}
        </p>
      ) : null}

      <form action={loginAction} className="mt-6 space-y-4">
        <input type="hidden" name="next" value={next} />
        <label className="block text-sm font-semibold">
          Correo
          <input
            name="email"
            type="email"
            required
            autoComplete="email"
            maxLength={254}
            placeholder="tu@example.com"
            className="mt-2 h-12 w-full rounded-md border border-line bg-surface px-4 text-base font-normal placeholder:text-ink-muted focus:border-primary focus:outline-none"
          />
        </label>
        <SubmitButton>Entrar</SubmitButton>
      </form>
    </div>
  );
}
