"""runner CLI 测试."""

from __future__ import annotations

import sys
from io import StringIO

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
