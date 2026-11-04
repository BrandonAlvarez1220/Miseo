import { describe, expect, it } from "vitest";

import { isActivePath } from "./navigation";

describe("isActivePath", () => {
  it.each([
    ["/", { href: "/", exact: true }, true],
    ["/cocina", { href: "/", exact: true }, false],
    ["/cocina", { href: "/cocina" }, true],
    ["/cocina/postres", { href: "/cocina" }, true],
    ["/cocinas", { href: "/cocina" }, false],
  ])("%s with %o -> %s", (path, item, expected) => {
    expect(isActivePath(path, item)).toBe(expected);
  });
});
