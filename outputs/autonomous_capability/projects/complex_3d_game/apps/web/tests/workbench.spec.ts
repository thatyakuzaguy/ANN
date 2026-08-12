import { expect, test } from "@playwright/test";

test("loads playable pong arena", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("3D PONG ARENA")).toBeVisible();
  const canvas = page.locator("canvas[aria-label='Playable 3D Pong arena']");
  await expect(canvas).toBeVisible();
  await expect(page.getByRole("button", { name: "Pause" })).toBeVisible();
});
