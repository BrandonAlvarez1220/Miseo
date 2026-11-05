import { LogIn, LogOut } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

import { logoutAction } from "./actions";
import { getSession } from "./current-user";

const ROLE_LABELS = { user: "Cocinero", moderator: "Moderador", admin: "Admin" } as const;

/** Account area of the top bar. Reads the session cookie: render inside <Suspense>. */
export async function UserMenu() {
  const session = await getSession();
  if (!session) {
    return (
      <Link href="/ingresar" className={buttonVariants({ variant: "secondary", size: "sm" })}>
        <LogIn aria-hidden="true" /> Ingresar
      </Link>
    );
  }
  const { user } = session;
  const initials = user.display_name.slice(0, 2).toUpperCase();
  return (
    <div className="flex items-center gap-2 sm:gap-3">
      <div className="flex items-center gap-2">
        <span
          aria-hidden="true"
          className="inline-flex size-9 items-center justify-center rounded-full bg-primary-soft text-xs font-bold text-primary"
        >
          {initials}
        </span>
        <span className="hidden leading-tight sm:block">
          <span className="block max-w-32 truncate text-sm font-semibold">{user.display_name}</span>
          <span className="block text-xs text-ink-muted">{ROLE_LABELS[user.role]}</span>
        </span>
      </div>
      <form action={logoutAction}>
        <button
          type="submit"
          aria-label="Cerrar sesión"
          title="Cerrar sesión"
          className="inline-flex size-9 items-center justify-center rounded-full border border-line text-ink-muted hover:bg-surface-muted hover:text-ink"
        >
          <LogOut aria-hidden="true" className="size-4" />
        </button>
      </form>
    </div>
  );
}

export function UserMenuFallback() {
  return (
    <div aria-hidden="true" className="h-9 w-24 animate-pulse rounded-full bg-surface-muted" />
  );
}
