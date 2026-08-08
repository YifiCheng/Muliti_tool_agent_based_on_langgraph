from pathlib import Path


def test_compare_script_exists() -> None:
    assert Path("scripts/compare_qwen_providers.py").exists()


def test_remote_smoke_script_exists() -> None:
    assert Path("scripts/smoke_remote_qwen.py").exists()