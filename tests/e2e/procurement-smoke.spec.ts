import { expect, test } from "@playwright/test";

test("core procurement workflow renders and responds", async ({ page, browser }) => {
  const consoleIssues: string[] = [];
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      consoleIssues.push(`${message.type()}: ${message.text()}`);
    }
  });

  await page.setViewportSize({ width: 1366, height: 900 });
  await page.goto("http://127.0.0.1:3000", { waitUntil: "networkidle" });
  await expect(page).toHaveTitle(/Thai Public Procurement Intelligence/);
  await expect(page.getByRole("heading", { name: /AI-powered search/ })).toBeVisible();

  await page.getByRole("link", { name: "Search", exact: true }).click();
  await page.waitForLoadState("networkidle");
  await page.getByPlaceholder("IT, construction, hospital").fill("IT");
  await expect(page.locator('section[aria-live="polite"]')).toContainText("IT");

  await page.getByRole("link", { name: /IT network upgrade/i }).first().click();
  await page.waitForLoadState("networkidle");
  await page.getByRole("button", { name: /Generate|Refresh/ }).click();
  await expect(page.getByText(/Project purpose/)).toBeVisible({ timeout: 5000 });

  await page.goto("http://127.0.0.1:3000/assistant", { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /^Ask$/ }).click();
  await expect(page.getByText(/Retrieved evidence/)).toBeVisible({ timeout: 5000 });

  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await mobile.goto("http://127.0.0.1:3000/records", { waitUntil: "networkidle" });
  await expect(mobile.getByRole("heading", { name: /Procurement Search/ })).toBeVisible();
  await mobile.close();

  expect(consoleIssues.filter((line) => !line.includes("Download the React DevTools"))).toEqual([]);
});

