import { Container } from "@/components/ui/container";

const REPOSITORY_URL = "https://github.com/BrandonAlvarez1220/Miseo";

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-line/60">
      <Container className="flex flex-col gap-2 py-8 text-sm text-ink-muted sm:flex-row sm:items-center sm:justify-between">
        <p>
          <span className="font-display font-semibold text-ink">Miseo</span> · Proyecto open source
          y comunitario.
        </p>
        <a href={REPOSITORY_URL} className="hover:text-ink" rel="noreferrer" target="_blank">
          Código fuente en GitHub
        </a>
      </Container>
    </footer>
  );
}
