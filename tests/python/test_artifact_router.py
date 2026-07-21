from agentic_engineering_network.orchestration.artifact_router import (
    ProjectKind,
    build_project_artifacts,
    classify_project_kind,
)


PONG_PROMPT = "Build me a fully functional 3d pong game with score and an ai player"


def test_classifies_pong_prompt_as_game() -> None:
    assert classify_project_kind(PONG_PROMPT) == ProjectKind.GAME


def test_game_prompt_generates_playable_game_instead_of_saas_dashboard() -> None:
    artifacts = build_project_artifacts(PONG_PROMPT, "9375cfc9")

    api_dockerfile = artifacts[next(path for path in artifacts if path.endswith("apps/api/Dockerfile"))]
    page = artifacts[next(path for path in artifacts if path.endswith("apps/web/src/app/page.tsx"))]
    readme = artifacts[next(path for path in artifacts if path.endswith("README.md"))]
    project_kind = artifacts[next(path for path in artifacts if path.endswith("docs/PROJECT_KIND.md"))]

    assert "ENV PYTHONPATH=/app" in api_dockerfile
    assert '"pip>=26.1.2"' in api_dockerfile
    assert "3D PONG ARENA" in page
    assert "canvas" in page
    assert "requestAnimationFrame" in page
    assert "AI WINS" in page
    assert "Generated SaaS App" not in page
    assert "New deal" not in page
    assert "playable game project, not a SaaS dashboard" in readme
    assert "project_kind: game" in project_kind


def test_saas_prompt_still_uses_saas_template() -> None:
    artifacts = build_project_artifacts("Build me a SaaS CRM", "12345678")

    page = artifacts["build-me-a-saas-crm-12345678/apps/web/src/app/page.tsx"]
    api_dockerfile = artifacts["build-me-a-saas-crm-12345678/apps/api/Dockerfile"]
    e2e = artifacts["build-me-a-saas-crm-12345678/apps/web/tests/workbench.spec.ts"]

    assert "Generated SaaS App" not in page
    assert "SaaS CRM" in page
    assert "New deal" in page
    assert '"pip>=26.1.2"' in api_dockerfile
    assert 'name: "New deal · draft", exact: true' in e2e


def test_complex_algorithm_prompt_routes_to_executable_algorithm_service() -> None:
    artifacts = build_project_artifacts(
        "Build a service implementing a complex algorithm with benchmarks and edge cases",
        "87654321",
    )

    algorithm = next(value for path, value in artifacts.items() if path.endswith("app/algorithm.py"))
    benchmark = next(value for path, value in artifacts.items() if path.endswith("benchmark.py"))
    dockerfile = next(value for path, value in artifacts.items() if path.endswith("Dockerfile"))
    compose = next(value for path, value in artifacts.items() if path.endswith("docker-compose.yml"))
    pyproject = next(value for path, value in artifacts.items() if path.endswith("pyproject.toml"))
    dockerignore = next(value for path, value in artifacts.items() if path.endswith(".dockerignore"))
    tests = [value for path, value in artifacts.items() if "/tests/test_" in path]

    assert "k_shortest_paths" in algorithm
    assert "O(K * V * (E log V))" in algorithm
    assert "run_benchmark" in benchmark
    assert '"pip>=26.1.2"' in dockerfile
    assert '".[test]"' in dockerfile
    assert "ENV PYTHONPATH=/app" in dockerfile
    assert "healthcheck:" in compose
    assert "XDG_CACHE_HOME: /tmp" in compose
    assert "pip-audit" in pyproject
    assert ".aen" in dockerignore
    assert "release" in dockerignore
    assert len(tests) >= 4
