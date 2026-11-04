import { describe, expect, it } from "vitest";

import { themeForPath } from "./modules";

describe("themeForPath", () => {
  it.each([
    ["/", "kitchen"],
    ["/cocina", "kitchen"],
    ["/mixologia", "mixology"],
    ["/mixologia/negroni", "mixology"],
    ["/mixologiax", "kitchen"],
  ])("%s -> %s", (path, theme) => {
    expect(themeForPath(path)).toBe(theme);
  });
});
