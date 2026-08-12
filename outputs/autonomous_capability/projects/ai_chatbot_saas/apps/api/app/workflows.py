from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowRule(BaseModel):
    field: str
    operator: Literal["eq", "neq", "gt", "lt", "contains"]
    value: str | int | float | bool


class WorkflowAction(BaseModel):
    type: Literal["create_task", "send_webhook", "assign_owner", "update_stage"]
    params: dict[str, Any] = Field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    name: str
    trigger: str
    rules: list[WorkflowRule] = Field(default_factory=list)
    actions: list[WorkflowAction] = Field(default_factory=list)


@dataclass(frozen=True)
class WorkflowDecision:
    matched: bool
    actions: list[WorkflowAction]


def _matches_rule(rule: WorkflowRule, event: dict[str, Any]) -> bool:
    current = event.get(rule.field)
    if rule.operator == "eq":
        return current == rule.value
    if rule.operator == "neq":
        return current != rule.value
    if rule.operator == "gt":
        return float(current or 0) > float(rule.value)
    if rule.operator == "lt":
        return float(current or 0) < float(rule.value)
    if rule.operator == "contains":
        return str(rule.value).lower() in str(current or "").lower()
    return False


def evaluate_workflow(definition: WorkflowDefinition, event: dict[str, Any]) -> WorkflowDecision:
    matched = event.get("trigger") == definition.trigger and all(_matches_rule(rule, event) for rule in definition.rules)
    return WorkflowDecision(matched=matched, actions=definition.actions if matched else [])


@router.post("/evaluate")
def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    definition = WorkflowDefinition.model_validate(payload["definition"])
    event = dict(payload.get("event", {}))
    decision = evaluate_workflow(definition, event)
    return {"matched": decision.matched, "actions": [action.model_dump() for action in decision.actions]}


@router.get("/templates")
def templates() -> list[WorkflowDefinition]:
    return [
        WorkflowDefinition(
            name="High value deal escalation",
            trigger="deal.updated",
            rules=[WorkflowRule(field="value", operator="gt", value=25000), WorkflowRule(field="stage", operator="eq", value="negotiation")],
            actions=[WorkflowAction(type="assign_owner", params={"role": "manager"}), WorkflowAction(type="create_task", params={"title": "Review high-value negotiation"})],
        )
    ]
