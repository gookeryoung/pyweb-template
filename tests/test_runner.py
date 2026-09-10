"""runner CLI 测试."""

from __future__ import annotations

import argparse
import sys
from io import StringIO
from unittest.mock import patch

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


def test_demo_plugins_discovers_builtin() -> None:
    """demo plugins 应发现两个内置插件."""
    rc = runner.demo_plugins()
    assert rc == 0


def test_demo_quickstart_success() -> None:
    """demo quickstart 应完整跑通."""
    rc = runner.demo_quickstart()
    assert rc == 0


def test_demo_unknown_subcommand_returns_error() -> None:
    """未知 demo 子命令应返回 1 并打印提示."""
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    try:
        rc = runner.run_demo_command("nonexistent")
        err = sys.stderr.getvalue()
    finally:
        sys.stderr = old_stderr
    assert rc == 1
    assert "未知 demo 子命令" in err


def test_dev_sets_reload_true() -> None:
    """dev 应把 args.reload 置 True 然后转发给 serve."""
    args = argparse.Namespace(host="127.0.0.1", port=8000, reload=False, workers=1)
    with patch.object(runner, "serve") as mock_serve:
        runner.dev(args)
        assert args.reload is True
        mock_serve.assert_called_once_with(args)


def test_serve_no_uvicorn_prints_error_and_exits() -> None:
    """uvicorn 缺失时应打印错误并 sys.exit(1)."""
    args = argparse.Namespace(host="127.0.0.1", port=8000, reload=False, workers=1)

    def raise_io(*_args: object, **_kwargs: object) -> None:
        raise ImportError("no uvicorn")

    with patch.dict("sys.modules", {"uvicorn": None}):
        with patch("builtins.__import__", side_effect=raise_io):
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


def test_main_demo_unknown_subcmd_argparse_exits_2() -> None:
    """main demo 子命令传 argparse 未知 choice 时由 argparse sys.exit(2)."""
    with patch.object(sys, "argv", ["pywt", "demo", "bogus"]):
        with pytest.raises(SystemExit) as excinfo:
            runner.main()
        # argparse invalid choice 行为 code=2
        assert excinfo.value.code == 2
