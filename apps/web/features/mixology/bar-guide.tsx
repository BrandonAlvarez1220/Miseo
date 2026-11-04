import { connection } from "next/server";

import { apiErrorState } from "@/components/ui/api-error-state";
import type { CatalogItem } from "@/types/api";

import { listGlassTypes, listTechniques } from "./api";

/** Techniques and glassware reference. Render inside <Suspense>. */
export async function BarGuide() {
  await connection();
  let techniques: CatalogItem[];
  let glasses: CatalogItem[];
  try {
    [techniques, glasses] = await Promise.all([listTechniques(), listGlassTypes()]);
  } catch (error) {
    return apiErrorState(error, "/mixologia", "la guía de barra");
  }
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <GuideList title="Técnicas" items={techniques} />
      <GuideList title="Cristalería" items={glasses} />
    </div>
  );
}

function GuideList({ title, items }: { title: string; items: CatalogItem[] }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <h3 className="mb-3 font-bold">{title}</h3>
      <dl className="divide-y divide-line">
        {items.map((item) => (
          <div key={item.slug} className="py-3 first:pt-0 last:pb-0">
            <dt className="font-medium">{item.name}</dt>
            {item.description ? (
              <dd className="mt-0.5 text-sm text-ink-muted">{item.description}</dd>
            ) : null}
          </div>
        ))}
      </dl>
    </div>
  );
}
