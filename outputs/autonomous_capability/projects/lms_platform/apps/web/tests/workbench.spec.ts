import { expect, test } from "@playwright/test";

test("loads domain dashboard and creates a record", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("LMS SaaS")).toBeVisible();
  const create = page.getByRole("button", { name: "New course" });
  await expect(create).toBeVisible();
  await create.click();
  await expect(page.getByRole("button", { name: "New course · draft", exact: true })).toBeVisible();
});
