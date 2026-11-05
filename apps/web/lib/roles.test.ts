import { describe, expect, it } from "vitest";

import { hasRole } from "./roles";

describe("hasRole", () => {
  it.each([
    ["admin", "admin", true],
    ["admin", "moderator", true],
    ["moderator", "moderator", true],
    ["moderator", "admin", false],
    ["user", "moderator", false],
    ["user", "user", true],
  ] as const)("%s vs %s -> %s", (actual, minimum, expected) => {
    expect(hasRole(actual, minimum)).toBe(expected);
  });
});
