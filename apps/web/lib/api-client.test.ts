import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch } from "./api-client";

function mockFetch(response: Response | Error) {
  const fn = vi.fn(() =>
    response instanceof Error ? Promise.reject(response) : Promise.resolve(response),
  );
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("apiFetch", () => {
  it("builds the URL from API_URL and skips empty query params", async () => {
    vi.stubEnv("API_URL", "http://api.test");
    const fetchMock = mockFetch(Response.json([]));

    await apiFetch("/api/v1/categories", { query: { recipe_type: "drink", page: undefined } });

    const [url] = fetchMock.mock.calls[0] as unknown as [URL];
    expect(url.toString()).toBe("http://api.test/api/v1/categories?recipe_type=drink");
  });

  it("sends the access token as a Bearer header only when given", async () => {
    // A fresh Response per call: a body can only be read once.
    const fetchMock = vi.fn(() => Promise.resolve(Response.json({})));
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("/api/v1/me", { token: "abc" });
    await apiFetch("/api/v1/recipes");

    const headers = (call: number) =>
      (fetchMock.mock.calls[call] as unknown as [URL, RequestInit])[1].headers as Record<
        string,
        string
      >;
    expect(headers(0).Authorization).toBe("Bearer abc");
    expect(headers(1).Authorization).toBeUndefined();
  });

  it("returns the parsed JSON body on success", async () => {
    mockFetch(Response.json([{ id: "1" }]));
    await expect(apiFetch("/x")).resolves.toEqual([{ id: "1" }]);
  });

  it("maps the uniform API error shape to ApiError", async () => {
    mockFetch(
      Response.json(
        { error: { code: "validation_error", message: "Request validation failed", details: [] } },
        { status: 422 },
      ),
    );

    const error = await apiFetch("/x").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 422, code: "validation_error" });
  });

  it("handles non-JSON error responses", async () => {
    mockFetch(new Response("Bad gateway", { status: 502 }));
    await expect(apiFetch("/x")).rejects.toMatchObject({ status: 502, code: "http_error" });
  });

  it("reports network failures as network_error", async () => {
    mockFetch(new TypeError("fetch failed"));
    await expect(apiFetch("/x")).rejects.toMatchObject({ status: 0, code: "network_error" });
  });
});
