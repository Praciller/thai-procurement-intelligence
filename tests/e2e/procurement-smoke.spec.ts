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
  await expect(page.getByText("Synthetic Demo Dataset", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: /AI-powered search/ })).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

  await page.getByRole("link", { name: "Search", exact: true }).click();
  await page.waitForLoadState("networkidle");
  await page.getByPlaceholder("IT, construction, hospital").fill("IT");
  await expect(page.locator('section[aria-live="polite"]')).toContainText("IT");
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

  await page.getByRole("link", { name: /IT network upgrade/i }).first().click();
  await page.waitForLoadState("networkidle");
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
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


test("keyboard navigation and localized search controls expose their state", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/records", { waitUntil: "networkidle" });

  const skipLink = page.getByRole("link", { name: "Skip to main content" });
  await page.keyboard.press("Tab");
  await expect(skipLink).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#main-content$/);
  await expect(page.locator("main#main-content")).toHaveAttribute("tabindex", "-1");

  await expect(page.getByRole("link", { name: "Search", exact: true })).toHaveAttribute("aria-current", "page");
  const keyword = page.getByRole("button", { name: "keyword", exact: true });
  const hybrid = page.getByRole("button", { name: "hybrid", exact: true });
  await expect(keyword).toHaveAttribute("aria-pressed", "true");
  await hybrid.click();
  await expect(hybrid).toHaveAttribute("aria-pressed", "true");
  await expect(keyword).toHaveAttribute("aria-pressed", "false");

  await page.goto("http://127.0.0.1:3000/records?lang=th", { waitUntil: "networkidle" });
  await expect(page.locator("html")).toHaveAttribute("lang", "th");
  await expect(page.getByRole("link", { name: "ข้ามไปยังเนื้อหาหลัก" })).toHaveCount(1);
  await expect(page.getByRole("link", { name: "TH", exact: true })).toHaveAttribute("aria-current", "true");
});

test("mobile pages keep horizontal scrolling inside record tables", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const expectNoPageOverflow = async (pageName: string) => {
    const widths = await page.evaluate(() => ({
      viewport: window.innerWidth,
      document: document.documentElement.scrollWidth,
      body: document.body.scrollWidth,
    }));
    expect(widths.document).toBeLessThanOrEqual(widths.viewport);
    expect(widths.body).toBeLessThanOrEqual(widths.viewport);
    console.log(`[mobile-overflow] ${pageName} ${JSON.stringify(widths)}`);
  };
  let recordId = "";
  await page.route("**/api/records?*", async (route) => {
    const url = new URL(route.request().url());
    if (url.searchParams.get("q") !== "คอมพิวเตอร์") {
      await route.continue();
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [{
          id: recordId,
          project_name: "คอมพิวเตอร์สำหรับระบบสารสนเทศและงานบริการภาครัฐระดับภูมิภาค",
          agency_name: "สำนักงานพัฒนาระบบสารสนเทศและบริการดิจิทัลภาครัฐ",
          province: "กรุงเทพมหานคร",
          procurement_category: "คอมพิวเตอร์และอุปกรณ์เครือข่าย",
          budget_amount: "1234567890",
          announcement_date: "2026-01-01",
        }],
        total: 1,
        page: 1,
        page_size: 20,
      }),
    });
  });

  await page.goto("http://127.0.0.1:3000/", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: /AI-powered search/ })).toBeVisible();
  const homeTable = page.locator("main .overflow-x-auto").first();
  await expect(homeTable).toBeVisible();
  await expect.poll(() => homeTable.evaluate((element) => element.scrollWidth > element.clientWidth)).toBe(true);
  await expectNoPageOverflow("home");

  await page.goto("http://127.0.0.1:3000/records?lang=en", { waitUntil: "networkidle" });
  const seededRecordLink = page.locator('section[aria-live="polite"] table tbody a').first();
  const existingRecordHref = await seededRecordLink.getAttribute("href");
  if (!existingRecordHref) throw new Error("Expected an existing record to open for the detail check");
  const seededRecordName = (await seededRecordLink.innerText()).trim();
  recordId = new URL(existingRecordHref, page.url()).pathname.split("/").at(-1) || "";
  await page.getByPlaceholder("IT, construction, hospital").fill("คอมพิวเตอร์");
  const fixtureProjectName = "คอมพิวเตอร์สำหรับระบบสารสนเทศและงานบริการภาครัฐระดับภูมิภาค";
  const fixtureProjectLink = page.getByRole("link", { name: fixtureProjectName, exact: true });
  await expect(fixtureProjectLink).toBeVisible();
  await expectNoPageOverflow("search results");
  const resultsTable = page.locator('section[aria-live="polite"] .overflow-x-auto');
  await expect.poll(() => resultsTable.evaluate((element) => element.scrollWidth > element.clientWidth)).toBe(true);
  const scrollPosition = await resultsTable.evaluate((element) => {
    const before = element.scrollLeft;
    element.scrollLeft = element.scrollWidth - element.clientWidth;
    return { before, after: element.scrollLeft, maxScrollLeft: element.scrollWidth - element.clientWidth };
  });
  expect(scrollPosition.maxScrollLeft).toBeGreaterThan(0);
  expect(scrollPosition.after).toBeGreaterThan(scrollPosition.before);

  await fixtureProjectLink.click();
  await page.waitForLoadState("networkidle");
  await expect(page).toHaveURL(/\/records\/[^?]+\?lang=en/);
  await expect(page.getByRole("heading", { name: seededRecordName, exact: true })).toBeVisible();
  await expectNoPageOverflow("record detail");
});
