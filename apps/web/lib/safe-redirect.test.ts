import { describe, expect, it } from "vitest";

import { safeRedirectPath } from "./safe-redirect";

describe("safeRedirectPath", () => {
  it.each([
    ["/recetas?q=sopa", "/recetas?q=sopa"],
    ["/rutas/cocina", "/rutas/cocina"],
    ["/", "/"],
  ])("keeps the same-site path %s", (input, expected) => {
    expect(safeRedirectPath(input)).toBe(expected);
  });

  it.each([
    "https://evil.example",
    "//evil.example",
    "/\\evil.example",
    "javascript:alert(1)",
    "recetas",
    "/ok\nSet-Cookie: x=1",
    "",
  ])("rejects %j", (input) => {
    expect(safeRedirectPath(input)).toBe("/");
  });

  it("handles missing values and custom fallbacks", () => {
    expect(safeRedirectPath(undefined)).toBe("/");
    expect(safeRedirectPath(null, "/rutas")).toBe("/rutas");
  });
});
