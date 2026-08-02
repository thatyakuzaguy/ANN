from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_api_images_include_git_for_repair_diff_validation() -> None:
    dockerfile = (ROOT / "docker" / "api.Dockerfile").read_text(encoding="utf-8")
    gpu_dockerfile = (ROOT / "docker" / "api.gpu.Dockerfile").read_text(encoding="utf-8")

    assert " git " in dockerfile or " git \\" in dockerfile
    assert " git " in gpu_dockerfile or " git \\" in gpu_dockerfile
    assert "docker:29.6.2-cli" in dockerfile
    assert "docker:29.6.2-cli" in gpu_dockerfile
    assert "golang:1.26.5-alpine AS compose-builder" in dockerfile
    assert "golang:1.26.5-alpine AS compose-builder" in gpu_dockerfile
    assert "github.com/docker/docker=/compat/docker" in dockerfile
    assert "github.com/docker/docker=/compat/docker" in gpu_dockerfile
    assert "COPY --from=docker-cli /usr/local/libexec/docker/cli-plugins/docker-compose" not in dockerfile
    assert "COPY --from=docker-cli /usr/local/libexec/docker/cli-plugins/docker-compose" not in gpu_dockerfile


def test_api_images_run_as_non_root_and_keep_socket_group_access() -> None:
    dockerfile = (ROOT / "docker" / "api.Dockerfile").read_text(encoding="utf-8")
    gpu_dockerfile = (ROOT / "docker" / "api.gpu.Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "USER ann" in dockerfile
    assert "USER ann" in gpu_dockerfile
    assert 'group_add:\n      - "0"' in compose


def test_compose_waits_for_the_real_api_health_endpoint() -> None:
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "http://localhost:8000/api/health" in compose
    assert "api:\n        condition: service_healthy" in compose


def test_gpu_image_limits_native_build_parallelism() -> None:
    gpu_dockerfile = (ROOT / "docker" / "api.gpu.Dockerfile").read_text(encoding="utf-8")

    assert "CMAKE_BUILD_PARALLEL_LEVEL=4" in gpu_dockerfile
    assert "apt-get upgrade -y" in gpu_dockerfile


def test_web_runtime_removes_unused_package_manager() -> None:
    dockerfile = (ROOT / "docker" / "web.Dockerfile").read_text(encoding="utf-8")

    assert "rm -rf /usr/local/lib/node_modules/npm" in dockerfile
    assert "rm -f /usr/local/bin/npm /usr/local/bin/npx" in dockerfile
