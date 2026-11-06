import { redirect } from "next/navigation";

import { hasRole } from "@/lib/roles";
import type { UserRole } from "@/types/api";

import { getSession, type Session } from "./current-user";

/**
 * For pages that need a signed-in user with at least ``minimum`` role.
 * Signed out -> sends them to the login and back. Signed in without the role -> null
 * (the page shows a "no permission" message). The API enforces the same rule.
 */
export async function requireRole(minimum: UserRole, returnTo: string): Promise<Session | null> {
  const session = await getSession();
  if (!session) redirect(`/ingresar?next=${encodeURIComponent(returnTo)}`);
  return hasRole(session.user.role, minimum) ? session : null;
}
