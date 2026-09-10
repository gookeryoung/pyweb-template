"""demos.cli_demo 测试."""

from __future__ import annotations

from pyweb_template.demos.cli_demo import run_crud_demo


def test_run_crud_demo_returns_success() -> None:
    """完整跑 CRUD demo 应 success=True."""
    result = run_crud_demo()
    assert result["success"] is True
    steps = {r["step"]: r["ok"] for r in result["results"]}
    assert all(steps.values())


def test_run_crud_demo_steps() -> None:
    """应包含所有预期步骤."""
    result = run_crud_demo()
    step_names = [r["step"] for r in result["results"]]
    assert "health" in step_names
    assert "create" in step_names
    assert "list" in step_names
    assert "get" in step_names
    assert "update" in step_names
    assert "delete" in step_names
    assert "plugins" in step_names
