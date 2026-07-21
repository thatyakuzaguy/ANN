from __future__ import annotations

from enum import StrEnum

from agentic_engineering_network.orchestration.algorithm_templates import (
    build_algorithm_project_artifacts,
)
from agentic_engineering_network.orchestration.game_templates import build_game_project_artifacts
from agentic_engineering_network.orchestration.project_templates import build_full_stack_project_artifacts


class ProjectKind(StrEnum):
    SAAS = "saas"
    GAME = "game"
    ALGORITHM_SERVICE = "algorithm_service"
    WEB_APP = "web_app"


GAME_KEYWORDS = {
    "game",
    "pong",
    "3d pong",
    "player",
    "score",
    "enemy",
    "ai opponent",
    "playable",
    "arcade",
    "shooter",
    "rpg",
    "platformer",
}


SAAS_KEYWORDS = {
    "saas",
    "crm",
    "ecommerce",
    "marketplace",
    "booking",
    "lms",
    "dashboard",
    "billing",
    "tenant",
}


ALGORITHM_KEYWORDS = {
    "algorithm",
    "algoritmo",
    "optimization",
    "optimisation",
    "shortest path",
    "route optimizer",
    "benchmark",
    "complexity",
}


def classify_project_kind(idea: str) -> ProjectKind:
    lower = idea.lower()
    game_score = sum(1 for keyword in GAME_KEYWORDS if keyword in lower)
    saas_score = sum(1 for keyword in SAAS_KEYWORDS if keyword in lower)
    algorithm_score = sum(1 for keyword in ALGORITHM_KEYWORDS if keyword in lower)
    if game_score and game_score >= saas_score:
        return ProjectKind.GAME
    if algorithm_score and algorithm_score >= saas_score:
        return ProjectKind.ALGORITHM_SERVICE
    if saas_score:
        return ProjectKind.SAAS
    return ProjectKind.WEB_APP


def build_project_artifacts(idea: str, run_id: str) -> dict[str, str]:
    kind = classify_project_kind(idea)
    if kind is ProjectKind.GAME:
        return build_game_project_artifacts(idea, run_id)
    if kind is ProjectKind.ALGORITHM_SERVICE:
        return build_algorithm_project_artifacts(idea, run_id)
    return build_full_stack_project_artifacts(idea, run_id)
