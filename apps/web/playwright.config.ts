import { defineConfig } from "@playwright/test";
import { existsSync } from "node:fs";

const windowsBrowser = process.platform === "win32"
  ? [
      process.env.ANN_PLAYWRIGHT_EXECUTABLE,
      "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
      "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"
    ].find((candidate): candidate is string => Boolean(candidate && existsSync(candidate)))
  : undefined;

export default defineConfig({
  testDir: "../../tests/e2e",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
    launchOptions: windowsBrowser ? { executablePath: windowsBrowser } : undefined
  },
  webServer: {
    command: "npm run dev",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: true,
    timeout: 120000
  }
});
