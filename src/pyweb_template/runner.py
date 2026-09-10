"""pyweb_template 命令行入口（pywt）.

子命令：
- serve              启动 uvicorn 服务器
- dev                开发模式（等价于 serve --reload）
- demo quickstart    串行跑最小 CRUD demo（启动->CRUD->清理）
- demo plugins       列出所有已发现插件（纯模块扫描，不启动服务器）
- info               打印版本/配置/运行环境

实现策略：argparse 标准库（避免引入 typer/click），子命令通过函数分发。
"""

from __future__ import annotations

import argparse
import sys


def serve(args: argparse.Namespace) -> None:
    """启动 uvicorn 服务器（生产可用，不依赖源码目录）."""
    try:
        import uvicorn
    except ImportError:
        print("[error] uvicorn 未安装，请执行 `uv sync`", file=sys.stderr)
        sys.exit(1)

    uvicorn.run(
        "pyweb_template.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=1 if args.reload else args.workers,
    )


def dev(args: argparse.Namespace) -> None:
    """开发模式（等价于 serve --reload）."""
    args.reload = True
    serve(args)


def demo_quickstart() -> int:
    """最小可运行 demo：启动服务器 -> CRUD 一条 User -> 清理退出."""
    try:
        from fastapi.testclient import TestClient
    except ImportError as exc:
        print(f"[error] demo 依赖未安装: {exc}", file=sys.stderr)
        print("        执行 `uv sync --extra demo`", file=sys.stderr)
        return 1

    from pyweb_template.app import app

    with TestClient(app) as client:
        # 1) 健康检查
        resp = client.get("/api/health")
        assert resp.status_code == 200 and resp.json().get("status") == "ok", resp.text

        # 2) 创建用户
        resp = client.post(
            "/api/v1/crud-demo/users",
            json={"username": "pywt-demo", "email": "demo@pywt.local", "role": "user"},
        )
        assert resp.status_code == 201, resp.text
        user = resp.json()
        user_id = user["id"]
        print(f"  [ok] 创建用户 id={user_id}")

        # 3) 查询列表
        resp = client.get("/api/v1/crud-demo/users")
        assert resp.status_code == 200, resp.text
        print(f"  [ok] 列表共 {len(resp.json()['items'])} 条")

        # 4) 查询单个
        resp = client.get(f"/api/v1/crud-demo/users/{user_id}")
        assert resp.status_code == 200 and resp.json()["username"] == "pywt-demo", resp.text
        print("  [ok] 查询单个用户")

        # 5) 更新
        resp = client.put(f"/api/v1/crud-demo/users/{user_id}", json={"email": "updated@pywt.local"})
        assert resp.status_code == 200 and resp.json()["email"] == "updated@pywt.local", resp.text
        print("  [ok] 更新用户邮箱")

        # 6) 删除
        resp = client.delete(f"/api/v1/crud-demo/users/{user_id}")
        assert resp.status_code == 204, resp.text
        print("  [ok] 删除用户")

        # 7) 插件列表
        resp = client.get("/api/plugins")
        assert resp.status_code == 200, resp.text
        plugins = [p["name"] for p in resp.json()["plugins"]]
        print(f"  [ok] 已加载插件: {plugins}")

    print("\n  demo quickstart 全部通过")
    return 0


def demo_plugins() -> int:
    """列出 plugins 目录下所有插件（纯文件扫描，不启动服务器）."""
    from pyweb_template.core.plugin_registry import plugin_registry

    plugin_registry.discover_and_load()
    infos = plugin_registry.get_plugin_info_list()
    print(f"共发现 {len(infos)} 个插件:\n")
    for info in infos:
        print(f"  - {info['name']:<16} v{info['version']:<8} {info['description']}")
    return 0


def run_demo_command(subcmd: str) -> int:
    """分发 demo 子命令."""
    if subcmd == "quickstart":
        return demo_quickstart()
    if subcmd == "plugins":
        return demo_plugins()
    print(f"[error] 未知 demo 子命令: {subcmd}", file=sys.stderr)
    print("        可用: quickstart / plugins", file=sys.stderr)
    return 1


def info_command() -> int:
    """打印版本/配置/运行环境."""
    import platform

    from pyweb_template.core.config import settings

    print(f"{settings.APP_NAME}  v{settings.APP_VERSION}")
    print("-" * 40)
    print(f"  Python:       {sys.version}")
    print(f"  Platform:     {platform.platform()}")
    print(f"  DEBUG:        {settings.DEBUG}")
    print(f"  DATABASE_URL: {settings.DATABASE_URL}")
    print(f"  API_PREFIX:   {settings.API_V1_PREFIX}")
    print(f"  AUTH_ENABLED: {settings.AUTH_ENABLED}")
    print(f"  PLUGINS_DIR:  {settings.PLUGINS_DIR}")
    print(f"  SYSLIB:       {sys.executable}")
    return 0


def main() -> None:
    """pywt CLI 入口."""
    parser = argparse.ArgumentParser(
        prog="pywt",
        description="pyweb-template - FastAPI + SQLAlchemy + Plugin 架构脚手架",
    )
    sub = parser.add_subparsers(dest="command")

    p_serve = sub.add_parser("serve", help="启动 uvicorn 服务器")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.add_argument("--workers", type=int, default=1)

    p_dev = sub.add_parser("dev", help="开发模式（serve + reload）")
    p_dev.add_argument("--host", default="127.0.0.1")
    p_dev.add_argument("--port", type=int, default=8000)

    p_demo = sub.add_parser("demo", help="运行内置 demo")
    p_demo.add_argument("subcmd", choices=["quickstart", "plugins"])

    sub.add_parser("info", help="打印版本/配置/运行环境")

    args = parser.parse_args()

    if args.command is None:
        args.host = "127.0.0.1"
        args.port = 8000
        args.reload = False
        args.workers = 1
        serve(args)
        return

    if args.command == "serve":
        serve(args)
    elif args.command == "dev":
        dev(args)
    elif args.command == "demo":
        sys.exit(run_demo_command(args.subcmd))
    elif args.command == "info":
        sys.exit(info_command())
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
