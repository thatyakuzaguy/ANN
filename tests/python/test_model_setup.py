from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from agentic_network.runtime_engine import model_setup


def _setup_root() -> Path:
    root = Path(r"D:\AgenticEngineeringNetwork\tests\.tmp\model-setup") / uuid4().hex
    (root / "config").mkdir(parents=True)
    (root / "config" / "ann_model_inventory.json").write_text(
        json.dumps({"version": 2, "models": []}),
        encoding="utf-8",
    )
    (root / "config" / "ann_model_policy.json").write_text(
        json.dumps(
            {
                "version": 1,
                "allow_real_model_load": False,
                "allow_model_download": False,
                "max_loaded_models": 1,
                "vram_policy": "SEQUENTIAL",
                "default_backend": "mock",
            }
        ),
        encoding="utf-8",
    )
    (root / "config" / "ann_runtime_engine.json").write_text(
        json.dumps(
            {
                "version": 1,
                "backend": "mock",
                "vram_policy": "SEQUENTIAL",
                "max_loaded_models": 1,
                "allow_parallel_llms": False,
                "backend_policy": {"allow_real_model_load": False, "allow_network": False},
            }
        ),
        encoding="utf-8",
    )
    return root


def test_register_local_gguf_uses_verified_hardlink_and_updates_inventory() -> None:
    root = _setup_root()
    source = root / "incoming" / "ann-test-q4_k_m.gguf"
    source.parent.mkdir()
    source.write_bytes(b"GGUF-test-model")

    result = model_setup.register_local_gguf(
        source_path=source,
        model_id="ann_test_coder",
        family="test",
        install_mode="hardlink",
        license_acknowledged=True,
        confirmed=True,
        risk_acknowledged=True,
        root=root,
    )

    destination = root / "models" / source.name
    assert result["status"] == "MODEL_REGISTERED"
    assert result["installed_by"] == "hardlink"
    assert result["sha256_verified"] is True
    assert result["downloads_performed"] is False
    assert result["model_load_performed"] is False
    assert destination.read_bytes() == source.read_bytes()
    inventory = json.loads((root / "config" / "ann_model_inventory.json").read_text(encoding="utf-8"))
    assert inventory["models"][0]["model_name"] == "ann_test_coder"
    assert inventory["models"][0]["path"] == f"models/{source.name}"


def test_register_local_gguf_bootstraps_missing_inventory_in_fresh_install() -> None:
    root = Path(r"D:\AgenticEngineeringNetwork\tests\.tmp\model-setup") / uuid4().hex
    root.mkdir(parents=True)
    source = root / "incoming" / "ann-fresh-install.gguf"
    source.parent.mkdir()
    source.write_bytes(b"GGUF-fresh-install")

    result = model_setup.register_local_gguf(
        source_path=source,
        model_id="ann_fresh_install",
        family="test",
        license_acknowledged=True,
        confirmed=True,
        risk_acknowledged=True,
        root=root,
    )

    inventory = json.loads((root / "config" / "ann_model_inventory.json").read_text(encoding="utf-8"))
    assert result["status"] == "MODEL_REGISTERED"
    assert inventory["version"] == 2
    assert [model["model_name"] for model in inventory["models"]] == ["ann_fresh_install"]


def test_fresh_install_model_state_uses_safe_read_only_defaults() -> None:
    root = Path(r"D:\AgenticEngineeringNetwork\tests\.tmp\model-setup") / uuid4().hex
    root.mkdir(parents=True)

    state = model_setup.get_model_setup_state(root)

    assert state["status"] == "PARTIAL"
    assert state["models"] == []
    assert state["runtime"] == {
        "backend": "mock",
        "allow_real_model_load": False,
        "vram_policy": "SEQUENTIAL",
        "max_loaded_models": 1,
    }
    assert len(state["configuration_warnings"]) == 3
    assert not (root / "config").exists()


def test_register_local_gguf_accepts_identical_concurrent_hardlink(monkeypatch) -> None:
    root = _setup_root()
    source = root / "incoming" / "ann-concurrent.gguf"
    source.parent.mkdir()
    source.write_bytes(b"GGUF-concurrent")
    real_link = model_setup.os.link

    def racing_link(link_source: Path, destination: Path) -> None:
        real_link(link_source, destination)
        raise FileExistsError(destination)

    monkeypatch.setattr(model_setup.os, "link", racing_link)
    result = model_setup.register_local_gguf(
        source_path=source,
        model_id="ann_concurrent_model",
        family="test",
        license_acknowledged=True,
        confirmed=True,
        risk_acknowledged=True,
        root=root,
    )

    assert result["status"] == "MODEL_REGISTERED"
    assert result["installed_by"] == "existing"


def test_model_registration_requires_license_acknowledgement_and_blocks_c_drive() -> None:
    root = _setup_root()
    source = root / "model.gguf"
    source.write_bytes(b"GGUF")

    with pytest.raises(ValueError, match="license"):
        model_setup.register_local_gguf(
            source_path=source,
            model_id="ann_test_model",
            family="test",
            license_acknowledged=False,
            confirmed=True,
            risk_acknowledged=True,
            root=root,
        )

    with pytest.raises(ValueError, match="D: or E:"):
        model_setup.register_local_gguf(
            source_path=r"C:\models\blocked.gguf",
            model_id="ann_test_model",
            family="test",
            license_acknowledged=True,
            confirmed=True,
            risk_acknowledged=True,
            root=root,
        )


@pytest.mark.parametrize(
    "raw_path",
    [
        r"\\server\share\model.gguf",
        r"\\?\D:\models\model.gguf",
        "//server/share/model.gguf",
    ],
)
def test_model_setup_blocks_unc_network_and_device_paths(raw_path: str) -> None:
    with pytest.raises(ValueError, match="UNC, network, and Windows device"):
        model_setup._safe_local_path(raw_path, require_exists=False, directory=False)


def test_managed_model_destination_cannot_escape_models_root() -> None:
    root = _setup_root()
    models_root = root / "models"
    models_root.mkdir()

    with pytest.raises(ValueError, match="single local path component"):
        model_setup._managed_model_destination(models_root, "../outside.gguf")


def test_atomic_configuration_write_does_not_leave_temporary_files() -> None:
    root = _setup_root()
    policy_path = root / "config" / "ann_model_policy.json"

    model_setup._write_json_atomic(policy_path, {"version": 1, "allow_real_model_load": False})

    assert json.loads(policy_path.read_text(encoding="utf-8"))["allow_real_model_load"] is False
    assert list(policy_path.parent.glob(f".{policy_path.name}.*.tmp")) == []


def test_runtime_activation_requires_gpu_ready_backend_and_preserves_sequential_policy(monkeypatch) -> None:
    root = _setup_root()
    source = root / "incoming" / "ann-test.gguf"
    source.parent.mkdir()
    source.write_bytes(b"GGUF-test-model")
    model_setup.register_local_gguf(
        source_path=source,
        model_id="ann_test_model",
        family="test",
        license_acknowledged=True,
        confirmed=True,
        risk_acknowledged=True,
        root=root,
    )
    monkeypatch.setattr(
        model_setup,
        "diagnose_llama_cpp_real_status",
        lambda _path: {"status": "READY", "errors": [], "LLAMA_SUPPORTS_GPU_OFFLOAD": True},
    )

    enabled = model_setup.configure_real_model_runtime(
        enabled=True,
        confirmed=True,
        risk_acknowledged=True,
        root=root,
    )

    assert enabled["status"] == "REAL_MODEL_RUNTIME_ENABLED"
    assert enabled["active_models"] == 0
    assert enabled["parallel_llm_loads"] == 0
    assert enabled["model_load_performed"] is False
    policy = json.loads((root / "config" / "ann_model_policy.json").read_text(encoding="utf-8"))
    runtime = json.loads((root / "config" / "ann_runtime_engine.json").read_text(encoding="utf-8"))
    assert policy["allow_real_model_load"] is True
    assert policy["max_loaded_models"] == 1
    assert policy["vram_policy"] == "SEQUENTIAL"
    assert runtime["backend"] == "llama_cpp"
    assert runtime["allow_parallel_llms"] is False
    state = model_setup.get_model_setup_state(root)
    assert state["models"][0]["load_allowed"] is True
    assert state["models"][0]["load_blocked_reason"] == "allowed_by_policy"


def test_runtime_activation_refuses_cpu_or_unknown_llama_cpp_backend(monkeypatch) -> None:
    root = _setup_root()
    source = root / "incoming" / "ann-test.gguf"
    source.parent.mkdir()
    source.write_bytes(b"GGUF-test-model")
    model_setup.register_local_gguf(
        source_path=source,
        model_id="ann_test_model",
        family="test",
        license_acknowledged=True,
        confirmed=True,
        risk_acknowledged=True,
        root=root,
    )
    monkeypatch.setattr(
        model_setup,
        "diagnose_llama_cpp_real_status",
        lambda _path: {"status": "CPU_ONLY", "errors": ["llama_cpp_native_gpu_offload_required"]},
    )

    with pytest.raises(RuntimeError, match="GPU-capable"):
        model_setup.configure_real_model_runtime(
            enabled=True,
            confirmed=True,
            risk_acknowledged=True,
            root=root,
        )

    policy = json.loads((root / "config" / "ann_model_policy.json").read_text(encoding="utf-8"))
    assert policy["allow_real_model_load"] is False
