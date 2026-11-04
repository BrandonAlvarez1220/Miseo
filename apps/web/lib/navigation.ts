import { ChefHat, House, Martini, type LucideIcon } from "lucide-react";

import { MODULES } from "@/lib/modules";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  /** Only highlight on an exact path match (e.g. the home page). */
  exact?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Inicio", icon: House, exact: true },
  { href: MODULES.cooking.href, label: MODULES.cooking.label, icon: ChefHat },
  { href: MODULES.drink.href, label: MODULES.drink.label, icon: Martini },
];

export function isActivePath(pathname: string, item: Pick<NavItem, "href" | "exact">): boolean {
  if (item.exact) return pathname === item.href;
  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}
