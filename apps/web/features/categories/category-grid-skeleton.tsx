import { Skeleton } from "@/components/ui/skeleton";

export function CategoryGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div role="status" aria-label="Cargando categorías">
      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: count }, (_, index) => (
          <li key={index} className="rounded-lg bg-surface p-5 shadow-soft">
            <Skeleton className="h-5 w-1/2" />
            <Skeleton className="mt-3 h-4 w-5/6" />
          </li>
        ))}
      </ul>
    </div>
  );
}
