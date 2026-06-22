import assert from "node:assert/strict";
import { test } from "node:test";

import { getDictionary, normalizeLocale, withLocale } from "../../apps/web/src/lib/i18n.js";

test("normalizes supported and unsupported locales", () => {
  assert.equal(normalizeLocale("th"), "th");
  assert.equal(normalizeLocale("en"), "en");
  assert.equal(normalizeLocale("fr"), "en");
  assert.equal(normalizeLocale(undefined), "en");
});

test("returns Thai copy when requested", () => {
  const dictionary = getDictionary("th");

  assert.equal(dictionary.shell.nav.home, "หน้าแรก");
  assert.equal(dictionary.home.stats.records, "ระเบียน");
});

test("exposes bilingual official and synthetic dataset labels", () => {
  assert.equal(getDictionary("en").common.officialDataset, "Official Snapshot Dataset");
  assert.equal(getDictionary("th").common.syntheticDataset, "ชุดข้อมูลสาธิตสังเคราะห์");
  assert.equal(getDictionary("th").assistantClient.officialSource, "แหล่งข้อมูลทางการ");
});

test("adds or replaces the lang query parameter", () => {
  assert.equal(withLocale("/records", "th"), "/records?lang=th");
  assert.equal(withLocale("/records?page_size=20", "th"), "/records?page_size=20&lang=th");
  assert.equal(withLocale("/records?lang=en&page_size=20", "th"), "/records?lang=th&page_size=20");
});
