"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface NavLinkProps {
  href: string;
  children: ReactNode;
  exact?: boolean;
}

export function NavLink({ href, children, exact = false }: NavLinkProps) {
  const pathname = usePathname();
  const active = exact ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "rounded-full px-3 py-2 text-sm font-medium transition-colors sm:px-4",
        active ? "bg-primary-soft text-primary" : "text-ink-muted hover:text-ink",
      )}
    >
      {children}
    </Link>
  );
}
