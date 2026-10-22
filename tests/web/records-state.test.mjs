import assert from "node:assert/strict";
import { test } from "node:test";

import { buildRecordsQuery, getRecordsPagination, updateRecordsSearchState } from "../../apps/web/src/lib/records-state.js";

const initial = {
  q: "bridge",
  province: "",
  category: "",
  mode: "keyword",
  sort: "budget_desc",
  page: 4,
};

test("filter, mode, and sort changes return to the first page", () => {
  assert.equal(updateRecordsSearchState(initial, { province: "Bangkok" }).page, 1);
  assert.equal(updateRecordsSearchState(initial, { mode: "hybrid" }).page, 1);
  assert.equal(updateRecordsSearchState(initial, { sort: "date_asc" }).page, 1);
});

test("ranked search keeps the requested page and omits unsupported sort order", () => {
  const query = new URLSearchParams(buildRecordsQuery({ ...initial, mode: "hybrid" }, 20).slice(1));

  assert.equal(query.get("page"), "4");
  assert.equal(query.get("page_size"), "20");
  assert.equal(query.get("q"), "bridge");
  assert.equal(query.get("sort"), null);
});

test("pagination reports total pages and the ranked window cap", () => {
  assert.deepEqual(getRecordsPagination(41, 2, 20, false, 5000), {
    totalPages: 3,
    hasRankedWindowLimit: false,
    nextDisabled: false,
  });
  assert.deepEqual(getRecordsPagination(5001, 250, 20, true, 5000), {
    totalPages: 250,
    hasRankedWindowLimit: true,
    nextDisabled: true,
  });
});
