import type { Metadata, Viewport } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";

import { AppSidebar } from "@/components/layout/app-sidebar";
import { AppTopbar } from "@/components/layout/app-topbar";
import { MobileTabBar } from "@/components/layout/mobile-tab-bar";
import { SiteFooter } from "@/components/layout/site-footer";

import "./globals.css";

const body = Plus_Jakarta_Sans({
  variable: "--font-body",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Miseo — Cocina y mixología comunitaria",
    template: "%s · Miseo",
  },
  description:
    "Descubre lo que puedes crear con lo que ya tienes. Recetas de cocina y cócteles, abiertas y hechas por la comunidad.",
  applicationName: "Miseo",
};

export const viewport: Viewport = {
  themeColor: "#ffffff",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={`${body.variable} h-full antialiased`}>
      <body className="flex min-h-full bg-canvas text-ink">
        <AppSidebar />
        <div className="flex min-w-0 flex-1 flex-col pb-20 lg:pb-0">
          <AppTopbar />
          <main className="flex-1">{children}</main>
          <SiteFooter />
        </div>
        <MobileTabBar />
      </body>
    </html>
  );
}
