import { expect, test } from "@playwright/test";

test("loads domain dashboard and creates a record", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Marketplace SaaS")).toBeVisible();
  const create = page.getByRole("button", { name: "New product" });
  await expect(create).toBeVisible();
  await create.click();
  await expect(page.getByRole("button", { name: "New product · draft", exact: true })).toBeVisible();
});
