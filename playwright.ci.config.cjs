// GitHub ubuntu-24.04 runners ship with Google Chrome.
// Use this config only in CI to avoid a redundant apt/browser install.
// Local/default Playwright usage remains unchanged.
const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./tests/e2e",
  timeout: 45_000,
  use: {
    browserName: "chromium",
    channel: "chrome",
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
