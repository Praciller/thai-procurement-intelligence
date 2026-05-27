import assert from "node:assert/strict";
import { test } from "node:test";

import { resolveApiUrl } from "../../apps/web/src/lib/api-url.js";

test("uses absolute API bases unchanged", () => {
  assert.equal(
    resolveApiUrl("/records", {
      apiBaseUrl: "https://api.example.test/api",
      hasWindow: false,
    }),
    "https://api.example.test/api/records",
  );
});

test("keeps relative API bases relative in the browser", () => {
  assert.equal(
    resolveApiUrl("/records", {
      apiBaseUrl: "/backend/api",
      hasWindow: true,
      siteUrl: "https://ignored.example.test",
    }),
    "/backend/api/records",
  );
});

test("expands relative API bases on the server with the Vercel deployment URL", () => {
  assert.equal(
    resolveApiUrl("/analytics/overview", {
      apiBaseUrl: "/backend/api",
      hasWindow: false,
      vercelUrl: "thai-procurement-intelligence.vercel.app",
    }),
    "https://thai-procurement-intelligence.vercel.app/backend/api/analytics/overview",
  );
});

test("uses the configured site URL before the Vercel deployment URL", () => {
  assert.equal(
    resolveApiUrl("/analytics/overview", {
      apiBaseUrl: "/backend/api",
      hasWindow: false,
      siteUrl: "https://public.example.test",
      vercelUrl: "preview.example.test",
    }),
    "https://public.example.test/backend/api/analytics/overview",
  );
});
