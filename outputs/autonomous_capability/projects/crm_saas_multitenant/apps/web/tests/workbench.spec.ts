import { expect, test } from "@playwright/test";

test("loads domain dashboard and creates a record", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("SaaS CRM")).toBeVisible();
  const create = page.getByRole("button", { name: "New deal" });
  await expect(create).toBeVisible();
  await create.click();
  await expect(page.getByRole("button", { name: "New deal · draft", exact: true })).toBeVisible();
});
