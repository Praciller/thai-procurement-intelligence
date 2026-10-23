import assert from "node:assert/strict";
import { test } from "node:test";

import { asApiResult } from "../../apps/web/src/lib/api-result.js";

test("keeps a real empty response distinct from an API failure", async () => {
  const emptyResponse = await asApiResult(async () => ({ items: [], total: 0 }));
  const outage = await asApiResult(async () => {
    throw new Error("API request failed: 503");
  });

  assert.deepEqual(emptyResponse, { ok: true, data: { items: [], total: 0 } });
  assert.deepEqual(outage, { ok: false, error: "API request failed: 503" });
});
