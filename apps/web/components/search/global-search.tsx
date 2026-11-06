import { Search } from "lucide-react";
import Form from "next/form";

/**
 * Site-wide recipe search. A plain GET form (enhanced by next/form for
 * client-side navigation), so it also works before JavaScript loads.
 */
export function GlobalSearch() {
  return (
    <Form action="/recetas" role="search" className="relative w-full max-w-md">
      <label htmlFor="global-search" className="sr-only">
        Buscar recetas
      </label>
      <Search
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 left-3.5 size-4.5 -translate-y-1/2 text-ink-muted"
      />
      <input
        id="global-search"
        name="q"
        type="search"
        placeholder="Buscar recetas o cócteles"
        maxLength={100}
        autoComplete="off"
        className="h-11 w-full rounded-full border border-line bg-surface-muted pr-4 pl-10 text-sm placeholder:text-ink-muted focus:border-primary focus:bg-surface focus:outline-none"
      />
    </Form>
  );
}
