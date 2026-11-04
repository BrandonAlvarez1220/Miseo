import { Skeleton } from "@/components/ui/skeleton";

export function CategoryGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div role="status" aria-label="Cargando categorías">
      <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: count }, (_, index) => (
          <li
            key={index}
            className="flex items-center gap-4 rounded-lg border border-line bg-surface p-4"
          >
            <Skeleton className="size-14 shrink-0" />
            <div className="flex-1">
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="mt-2 h-3 w-5/6" />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
