import {
  BookOpen,
  ChefHat,
  GraduationCap,
  House,
  Martini,
  Refrigerator,
  type LucideIcon,
} from "lucide-react";

import { MODULES } from "@/lib/modules";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  /** Only highlight on an exact path match (e.g. the home page). */
  exact?: boolean;
  /** Hidden in the mobile tab bar (space for five items); search covers it. */
  desktopOnly?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Inicio", icon: House, exact: true },
  { href: "/que-puedo-preparar", label: "Qué preparo", icon: Refrigerator },
  { href: "/rutas", label: "Rutas", icon: GraduationCap },
  { href: "/recetas", label: "Recetas", icon: BookOpen, desktopOnly: true },
  { href: MODULES.cooking.href, label: MODULES.cooking.label, icon: ChefHat },
  { href: MODULES.drink.href, label: MODULES.drink.label, icon: Martini },
];

export function isActivePath(pathname: string, item: Pick<NavItem, "href" | "exact">): boolean {
  if (item.exact) return pathname === item.href;
  return pathname === item.href || pathname.startsWith(`${item.href}/`);
}
