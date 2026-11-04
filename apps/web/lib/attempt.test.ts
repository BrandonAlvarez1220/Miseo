import { describe, expect, it } from "vitest";

import { attempt } from "./attempt";

describe("attempt", () => {
  it("wraps success and failure", async () => {
    await expect(attempt(Promise.resolve(1))).resolves.toEqual({ ok: true, data: 1 });
    const failure = new Error("boom");
    await expect(attempt(Promise.reject(failure))).resolves.toEqual({ ok: false, error: failure });
  });
});
