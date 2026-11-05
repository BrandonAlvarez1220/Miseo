import type { UserRole } from "@/types/api";

const RANK: Record<UserRole, number> = { user: 0, moderator: 1, admin: 2 };

/** admin > moderator > user. The API enforces this too: this only decides what to show. */
export function hasRole(actual: UserRole, minimum: UserRole): boolean {
  return RANK[actual] >= RANK[minimum];
}
