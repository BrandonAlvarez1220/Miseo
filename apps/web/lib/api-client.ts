import type { ApiErrorBody } from "@/types/api";

/** Error raised for any non-successful API interaction. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly details: unknown = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Base URL of the API for server-side requests. Read at call time (not at
 * module load) so the same build works in every environment.
 */
export function getApiBaseUrl(): string {
  return process.env.API_URL ?? "http://localhost:8000";
}

function isApiErrorBody(value: unknown): value is ApiErrorBody {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as ApiErrorBody).error?.code === "string"
  );
}

type QueryValue = string | number | boolean | undefined | null;

export async function apiFetch<T>(
  path: string,
  options: {
    query?: Record<string, QueryValue>;
    init?: RequestInit;
    /** Access token for protected endpoints (sent as a Bearer header). */
    token?: string;
  } = {},
): Promise<T> {
  const url = new URL(path, getApiBaseUrl());
  for (const [key, value] of Object.entries(options.query ?? {})) {
    if (value !== undefined && value !== null) url.searchParams.set(key, String(value));
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options.init,
      headers: {
        Accept: "application/json",
        ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
        ...options.init?.headers,
      },
    });
  } catch (cause) {
    throw new ApiError("No se pudo conectar con la API", 0, "network_error", String(cause));
  }

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    if (isApiErrorBody(body)) {
      throw new ApiError(body.error.message, response.status, body.error.code, body.error.details);
    }
    throw new ApiError(`La API respondió ${response.status}`, response.status, "http_error");
  }

  return (await response.json()) as T;
}
