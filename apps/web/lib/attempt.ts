export type Attempt<T> = { ok: true; data: T } | { ok: false; error: unknown };

/**
 * Await a data load and capture its failure as a value, so components can
 * branch on it *outside* try/catch (JSX built inside a try block would not
 * have its rendering errors caught there, which is misleading).
 */
export async function attempt<T>(promise: Promise<T>): Promise<Attempt<T>> {
  try {
    return { ok: true, data: await promise };
  } catch (error) {
    return { ok: false, error };
  }
}
