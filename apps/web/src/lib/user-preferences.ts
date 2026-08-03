export const ANN_UI_PREFERENCES_KEY = "ann.ui-preferences.v1";

export type ApprovalMode = "full" | "supervised";

export type UiPreferences = {
  activePage: string;
  terminalOpen: boolean;
  selectedRunId: string | null;
  workspaceDirectory: string;
  approvalMode: ApprovalMode;
};

export const DEFAULT_UI_PREFERENCES: UiPreferences = {
  activePage: "pipeline",
  terminalOpen: true,
  selectedRunId: null,
  workspaceDirectory: "D:\\AgenticEngineeringNetwork\\generated-projects",
  approvalMode: "supervised",
};

const PAGE_IDS = new Set([
  "dashboard",
  "projects",
  "pipeline",
  "models",
  "knowledge",
  "runtime",
  "artifacts",
  "approvals",
  "logs",
  "settings",
]);

export function normalizeUserWorkspace(value: unknown): string {
  if (typeof value !== "string") return DEFAULT_UI_PREFERENCES.workspaceDirectory;
  const normalized = value.trim().replaceAll("/", "\\");
  if (!/^[DE]:\\/i.test(normalized) || /[<>:\"|?*\r\n]/.test(normalized.slice(3))) {
    return DEFAULT_UI_PREFERENCES.workspaceDirectory;
  }
  const segments = normalized.slice(3).split("\\").filter(Boolean);
  if (segments.length === 0 || segments.some(segment => segment === "." || segment === "..")) {
    return DEFAULT_UI_PREFERENCES.workspaceDirectory;
  }
  return normalized.replace(/\\+$/, "");
}

export function parseUiPreferences(value: string | null): UiPreferences {
  if (!value) return { ...DEFAULT_UI_PREFERENCES };
  try {
    const parsed = JSON.parse(value) as Partial<UiPreferences>;
    return {
      activePage: typeof parsed.activePage === "string" && PAGE_IDS.has(parsed.activePage)
        ? parsed.activePage
        : DEFAULT_UI_PREFERENCES.activePage,
      terminalOpen: typeof parsed.terminalOpen === "boolean"
        ? parsed.terminalOpen
        : DEFAULT_UI_PREFERENCES.terminalOpen,
      selectedRunId: typeof parsed.selectedRunId === "string" && parsed.selectedRunId.trim()
        ? parsed.selectedRunId.trim()
        : null,
      workspaceDirectory: normalizeUserWorkspace(parsed.workspaceDirectory),
      approvalMode: parsed.approvalMode === "full" ? "full" : "supervised",
    };
  } catch {
    return { ...DEFAULT_UI_PREFERENCES };
  }
}

export function readUiPreferences(): UiPreferences {
  if (typeof window === "undefined") return { ...DEFAULT_UI_PREFERENCES };
  return parseUiPreferences(window.localStorage.getItem(ANN_UI_PREFERENCES_KEY));
}

export function writeUiPreferences(preferences: UiPreferences): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ANN_UI_PREFERENCES_KEY, JSON.stringify(preferences));
}
