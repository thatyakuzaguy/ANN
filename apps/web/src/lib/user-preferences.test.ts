import { describe, expect, it } from "vitest";
import {
  DEFAULT_UI_PREFERENCES,
  normalizeUserWorkspace,
  parseUiPreferences,
} from "./user-preferences";

describe("ANN UI preferences", () => {
  it("restores valid interaction settings", () => {
    const result = parseUiPreferences(JSON.stringify({
      activePage: "approvals",
      terminalOpen: false,
      selectedRunId: "run-123",
      workspaceDirectory: "E:/ANN Projects/customer-portal",
      approvalMode: "full",
    }));

    expect(result).toEqual({
      activePage: "approvals",
      terminalOpen: false,
      selectedRunId: "run-123",
      workspaceDirectory: "E:\\ANN Projects\\customer-portal",
      approvalMode: "full",
    });
  });

  it("rejects malformed pages, modes, JSON, and C drive workspaces", () => {
    expect(parseUiPreferences("not-json")).toEqual(DEFAULT_UI_PREFERENCES);
    expect(parseUiPreferences(JSON.stringify({
      activePage: "admin",
      workspaceDirectory: "C:\\Users\\public",
      approvalMode: "automatic",
    }))).toMatchObject(DEFAULT_UI_PREFERENCES);
    expect(normalizeUserWorkspace("C:/Temp/project")).toBe(DEFAULT_UI_PREFERENCES.workspaceDirectory);
  });

  it("accepts only absolute D or E drive directories", () => {
    expect(normalizeUserWorkspace("D:/Projects/CRM/")).toBe("D:\\Projects\\CRM");
    expect(normalizeUserWorkspace("E:\\Archive\\ANN")).toBe("E:\\Archive\\ANN");
    expect(normalizeUserWorkspace("../escape")).toBe(DEFAULT_UI_PREFERENCES.workspaceDirectory);
    expect(normalizeUserWorkspace("D:\\Projects\\..\\escape")).toBe(DEFAULT_UI_PREFERENCES.workspaceDirectory);
  });
});
