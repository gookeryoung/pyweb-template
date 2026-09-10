"""runner CLI 测试."""

from __future__ import annotations

import argparse
import subprocess
import sys
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from pyweb_template import runner


def test_info_command_prints_version() -> None:
    """info 子命令应成功返回."""
    old_out = sys.stdout
    sys.stdout = StringIO()
    try:
        rc = runner.info_command()
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_out
    assert rc == 0
    assert "pyweb_template" in output


def test_dev_starts_backend_and_frontend_subprocess() -> None:
    """dev 应启动 backend + frontend 两个子进程."""
    args = argparse.Namespace(host="127.0.0.1", port=8000, reload=False, workers=1)
    mock_backend = Mock()
    mock_backend.pid = 12345
    mock_backend.wait.return_value = None  # 立即返回，不阻塞

    with (
        patch.object(runner, "_ensure_dev_env"),
        patch.object(subprocess, "Popen", return_value=mock_backend) as mock_popen,
    ):
        runner.dev(args)
        # Popen 应被调用两次：backend 和 frontend
        assert mock_popen.call_count == 2


def test_serve_no_uvicorn_prints_error_and_exits() -> None:
    """uvicorn 缺失时应打印错误并 sys.exit(1)."""
    args = argparse.Namespace(host="127.0.0.1", port=8000, reload=False, workers=1)

    def raise_io(*args: object, **kwargs: object) -> None:
        raise ImportError("no uvicorn")

    with (
        patch.dict("sys.modules", {"uvicorn": None}),
        patch("builtins.__import__", side_effect=raise_io),
    ):
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            with pytest.raises(SystemExit) as excinfo:
                runner.serve(args)
            assert excinfo.value.code == 1
        finally:
            sys.stderr = old_stderr


def test_main_with_no_command_defaults_to_serve() -> None:
    """main 无参数时应走 serve 路径."""
    with patch.object(runner, "serve") as mock_serve:
        with patch.object(sys, "argv", ["pywt"]):
            runner.main()
        mock_serve.assert_called_once()


def test_main_info_subcommand_exits_0() -> None:
    """main info 子命令应走 info_command 并 sys.exit(0)."""
    with patch.object(sys, "argv", ["pywt", "info"]):
        with pytest.raises(SystemExit) as excinfo:
            runner.main()
        assert excinfo.value.code == 0


def test_main_serve_subcommand_dispatches() -> None:
    """main serve 子命令应调用 serve."""
    with patch.object(runner, "serve") as mock_serve:
        with patch.object(sys, "argv", ["pywt", "serve", "--port", "9000"]):
            runner.main()
        mock_serve.assert_called_once()


def test_main_dev_subcommand_dispatches() -> None:
    """main dev 子命令应调用 dev（启动前后端子进程）."""
    with patch.object(runner, "dev") as mock_dev:
        with patch.object(sys, "argv", ["pywt", "dev", "--port", "9000"]):
            runner.main()
        mock_dev.assert_called_once()
