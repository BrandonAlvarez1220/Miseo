import { REPOSITORY_URL } from "@/lib/site";

export function SiteFooter() {
  return (
    <footer className="mt-20 border-t border-line px-4 py-8 text-sm text-ink-muted sm:px-6 lg:px-8">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p>
          <span className="font-semibold text-ink">Miseo</span> · Proyecto open source y
          comunitario.
        </p>
        <a href={REPOSITORY_URL} className="hover:text-ink" rel="noreferrer" target="_blank">
          Código fuente en GitHub
        </a>
      </div>
    </footer>
  );
}
