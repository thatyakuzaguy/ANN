import { NextRequest, NextResponse } from "next/server";
import {
  blockedShellAttemptResponse,
  classifyTerminalInput,
  getOrCreateSession,
  handleConversationMessage,
  handleModeCommand,
  normalizeWorkspaceDirectory,
  runSafeTerminalCommand,
  type ApprovalMode,
  type TerminalInputMode,
} from "@/lib/ann-terminal";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function isTerminalInputMode(value: unknown): value is TerminalInputMode {
  return value === "auto" || value === "chat" || value === "command";
}

function isApprovalMode(value: unknown): value is ApprovalMode {
  return value === "full" || value === "supervised";
}

export async function POST(request: NextRequest) {
  const body = (await request.json().catch(() => ({}))) as {
    conversation_id?: string;
    message?: string;
    mode?: TerminalInputMode;
    active_project?: string | null;
    workspace_directory?: string | null;
    approval_mode?: ApprovalMode;
  };

  const session = getOrCreateSession(body.conversation_id ?? "ann-terminal");
  if (isTerminalInputMode(body.mode)) session.currentMode = body.mode;
  const requestedWorkspace = body.workspace_directory ?? body.active_project;
  if (typeof requestedWorkspace === "string" && requestedWorkspace.trim()) {
    session.activeProject = normalizeWorkspaceDirectory(requestedWorkspace);
  }
  if (isApprovalMode(body.approval_mode)) session.approvalMode = body.approval_mode;

  const message = String(body.message ?? "").trim();
  const classification = classifyTerminalInput(message, session.currentMode);

  if (classification === "EMPTY") {
    return NextResponse.json({
      status: "skipped",
      input_classification: classification,
      display_message: "",
      events: [],
    }, { headers: { "Cache-Control": "no-store" } });
  }

  if (classification === "MALFORMED_INPUT") {
    return NextResponse.json({
      status: "blocked",
      input_classification: classification,
      display_message: "Blocked: input is not a registered ANN command in command mode.",
      events: [{ kind: "error", text: "Malformed or unsupported terminal input blocked." }],
    }, { headers: { "Cache-Control": "no-store" } });
  }

  if (classification === "EXPLICIT_SHELL_ATTEMPT") {
    return NextResponse.json(blockedShellAttemptResponse(message, session), {
      headers: { "Cache-Control": "no-store" },
    });
  }

  if (classification === "BUILTIN_COMMAND") {
    if (message.toLowerCase().startsWith("mode ") || message.toLowerCase().startsWith("chat")) {
      return NextResponse.json({
        ...handleModeCommand(message, session),
        input_classification: classification,
        terminal_status: { mode: session.currentMode },
      }, { headers: { "Cache-Control": "no-store" } });
    }
    const result = runSafeTerminalCommand(message, session);
    return NextResponse.json({
      status: "completed",
      input_classification: classification,
      display_message: result.lines.join("\n"),
      command_result: result,
      events: result.lines.map((text) => ({ kind: text.startsWith("Blocked:") ? "error" : "command", text })),
      terminal_status: { mode: session.currentMode },
    }, { headers: { "Cache-Control": "no-store" } });
  }

  if (classification === "ANN_SAFE_COMMAND") {
    const result = runSafeTerminalCommand(message, session);
    return NextResponse.json({
      status: "completed",
      input_classification: classification,
      display_message: result.lines.join("\n"),
      command_result: result,
      events: result.lines.map((text) => ({ kind: text.startsWith("Blocked:") ? "error" : "command", text })),
      terminal_status: { mode: session.currentMode },
    }, { headers: { "Cache-Control": "no-store" } });
  }

  return NextResponse.json(await handleConversationMessage(message, session), {
    headers: { "Cache-Control": "no-store" },
  });
}
