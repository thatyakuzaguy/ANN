import { expect, test } from "@playwright/test";

test("loads the ANN workbench and Approval Center", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("banner").getByText("ANN", { exact: true })).toBeVisible();
  await expect(page.getByRole("textbox", { name: "Write naturally or enter ANN command" })).toBeVisible();

  await page.getByRole("button", { name: "Approvals" }).click();

  await expect(page.getByRole("heading", { name: "Approval Center" })).toBeVisible();
});
