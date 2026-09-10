#!/usr/bin/env python3
"""一键串行跑所有 demo.

用法：`python scripts/run_demo.py`（需要先 `uv sync`）。
适合在 CI smoke 阶段或首次克隆仓库时跑一遍，确认框架全通。
"""

from __future__ import annotations

import sys

from pyweb_template.demos.cli_demo import run_crud_demo


def main() -> int:
    print("=" * 48)
    print("  pyweb-template built-in demos")
    print("=" * 48)

    # Demo 1: info
    from pyweb_template.runner import info_command

    print("\n[1/3] info...")
    info_command()

    # Demo 2: plugins 列表（纯模块扫描）
    from pyweb_template.runner import demo_plugins

    print("\n[2/3] plugin discovery...")
    demo_plugins()

    # Demo 3: CRUD quickstart
    print("\n[3/3] CRUD quickstart...")
    outcome = run_crud_demo()
    for r in outcome["results"]:
        mark = "ok" if r["ok"] else "FAIL"
        print(f"  [{mark}] {r['step']}")

    print()
    if outcome["success"]:
        print("All demos passed.")
        return 0
    print("Some demos FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
