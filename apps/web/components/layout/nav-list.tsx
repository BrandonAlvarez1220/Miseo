"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { isActivePath, NAV_ITEMS } from "@/lib/navigation";
import { cn } from "@/lib/utils";

type Variant = "sidebar" | "tabbar";

const styles: Record<Variant, { list: string; link: string; active: string; idle: string }> = {
  sidebar: {
    list: "flex flex-col gap-1",
    link: "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors [&_svg]:size-5",
    active: "bg-primary-soft text-primary",
    idle: "text-ink-muted hover:bg-surface-muted hover:text-ink",
  },
  tabbar: {
    list: "grid auto-cols-fr grid-flow-col",
    link: "flex flex-col items-center gap-1 py-2 text-[11px] font-medium [&_svg]:size-5",
    active: "text-primary",
    idle: "text-ink-muted",
  },
};

/**
 * Navigation links. `pathname` is read on the client to highlight the current
 * section; render inside <Suspense> with NavListFallback because pathname reads
 * suspend while prerendering dynamic routes.
 */
export function NavList({ variant }: { variant: Variant }) {
  return <NavLinks variant={variant} pathname={usePathname()} />;
}

/** Same links without active state, used as the Suspense fallback. */
export function NavListFallback({ variant }: { variant: Variant }) {
  return <NavLinks variant={variant} pathname={null} />;
}

function NavLinks({ variant, pathname }: { variant: Variant; pathname: string | null }) {
  const style = styles[variant];
  return (
    <ul className={style.list}>
      {NAV_ITEMS.map((item) => {
        const active = pathname !== null && isActivePath(pathname, item);
        const Icon = item.icon;
        return (
          <li key={item.href}>
            <Link
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(style.link, active ? style.active : style.idle)}
            >
              <Icon aria-hidden="true" />
              {item.label}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
