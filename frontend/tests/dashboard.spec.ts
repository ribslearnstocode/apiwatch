import { expect, test } from "@playwright/test";

test("real backend: create, edit, pause, enable, search and delete", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.getByText("Connected", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Add endpoint", exact: true }).click();
  await page.getByLabel("Monitor name").fill("Browser workflow API");
  await page
    .getByLabel("Public API endpoint")
    .fill("https://httpbin.org/anything/apiwatch-browser-test");
  await page.getByLabel("Enable automatic monitoring").uncheck();
  await page.getByRole("button", { name: "Create monitor" }).click();
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await expect(
    page.getByText("Browser workflow API", { exact: true }).first(),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Edit Browser workflow API", exact: true })
    .click();
  await page.getByLabel("Monitor name").fill("Renamed browser API");
  await page.getByLabel("Check interval (seconds)").fill("120");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(
    page.getByRole("button", {
      name: "Enable Renamed browser API",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Enable Renamed browser API", exact: true })
    .click();
  await expect(
    page.getByRole("button", {
      name: "Pause Renamed browser API",
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Check Renamed browser API", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Check completed.", {
    timeout: 25000,
  });
  await page
    .getByRole("button", { name: "Pause Renamed browser API", exact: true })
    .click();
  await expect(
    page.getByRole("button", {
      name: "Enable Renamed browser API",
      exact: true,
    }),
  ).toBeVisible();
  await page.getByLabel("Search monitors").fill("Renamed browser");
  await expect(page.getByText("Showing 1 of")).toBeVisible();
  await page
    .getByRole("button", { name: "Delete Renamed browser API", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Delete endpoint", exact: true })
    .click();
  await expect(page.getByText("No matching endpoints")).toBeVisible();
  expect(errors).toEqual([]);
});

test("analytics, filters, screenshot and mobile layout", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Connected", { exact: true })).toBeVisible();
  await page.getByLabel("Time range").selectOption("168");
  await page.getByLabel("Filter by status").selectOption("inactive");
  await expect(
    page.getByText("Demo · DummyJSON", { exact: true }).first(),
  ).toBeVisible();
  await page.getByLabel("Filter by status").selectOption("all");
  await page
    .locator(".endpoint-name")
    .filter({ hasText: "Demo · JSONPlaceholder" })
    .click();
  await expect(
    page.getByText("HTTP 503 (simulated)", { exact: true }),
  ).toBeVisible();
  await expect(page.locator(".recharts-area")).toBeVisible();
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0);
  await page.screenshot({
    path: "../docs/screenshots/dashboard-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "../docs/screenshots/dashboard-mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.getByRole("button", { name: "Add endpoint", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
});

test("backend failure is visible and recoverable", async ({ page }) => {
  await page.route("**/api/dashboard/summary*", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        detail: "Database unavailable. Please try again shortly.",
      }),
    }),
  );
  await page.goto("/");
  await expect(page.getByRole("alert")).toContainText("Database unavailable");
  await page.unroute("**/api/dashboard/summary*");
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.getByText("Connected", { exact: true })).toBeVisible();
});
