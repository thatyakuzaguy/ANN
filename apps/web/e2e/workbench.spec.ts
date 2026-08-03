import { expect, test } from "@playwright/test";

test("loads the ANN workbench and Approval Center", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("banner").getByText("ANN", { exact: true })).toBeVisible();
  await expect(page.getByRole("textbox", { name: "Write naturally or enter ANN command" })).toBeVisible();

  await page.getByRole("button", { name: "Approvals" }).click();

  await expect(page.getByRole("heading", { name: "Approval Center" })).toBeVisible();
});

test("exposes persistent run controls and keyboard navigation", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("textbox", { name: "Project workspace directory" })).toHaveValue(/^[DE]:\\/);
  await expect(page.getByRole("group", { name: "Approval mode" })).toBeVisible();

  await page.keyboard.press("Control+Shift+A");
  await expect(page.getByRole("heading", { name: "Approval Center" })).toBeVisible();

  await page.getByRole("button", { name: "Show keyboard shortcuts" }).click();
  await expect(page.getByRole("heading", { name: "ANN keyboard shortcuts" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("heading", { name: "ANN keyboard shortcuts" })).toBeHidden();

  await page.keyboard.press("Control+J");
  await expect(page.getByRole("textbox", { name: "Write naturally or enter ANN command" })).toBeHidden();
  await page.keyboard.press("Control+J");
  await expect(page.getByRole("textbox", { name: "Write naturally or enter ANN command" })).toBeVisible();
});
