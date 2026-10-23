import assert from "node:assert/strict";
import { test } from "node:test";

import { requireKnownDatasetMode } from "../../apps/web/src/lib/dataset-status.js";

test("does not infer synthetic mode from failed or unknown status responses", () => {
  const outage = requireKnownDatasetMode({ ok: false, error: "offline" });
  const unknown = requireKnownDatasetMode({ ok: true, data: { dataset_mode: "unknown" } });

  assert.deepEqual(outage, { ok: false, error: "offline" });
  assert.deepEqual(unknown, { ok: false, error: "API returned an unsupported dataset mode" });
});

test("accepts only supported dataset modes", () => {
  const official = { ok: true, data: { dataset_mode: "official_snapshot" } };

  assert.equal(requireKnownDatasetMode(official), official);
});

test("null and malformed dataset responses are unavailable rather than crashing", () => {
  for (const data of [null, {}, { dataset_mode: "legacy" }]) {
    const outcome = requireKnownDatasetMode({ ok: true, data });
    assert.deepEqual(outcome, {
      ok: false,
      error: "API returned an unsupported dataset mode",
    });
  }
});
