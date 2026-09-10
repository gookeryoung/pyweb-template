"""pyweb_template FastAPI 应用入口.

职责：
- 组装 FastAPI app（配置/中间件/lifespan）
- 在 lifespan 中自动发现并挂载所有插件
- 暴露框架级元路由（/api/health /api/plugins /api/demos /api/navigation）
- 不承载业务逻辑，业务由 plugins 按需挂载

启动方式：
- pywt serve（CLI 入口，见 runner.py）
- uvicorn pyweb_template.app:app --reload
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pyweb_template.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """应用生命周期管理."""
    from pyweb_template.core.plugin_registry import plugin_registry

    if settings.PLUGINS_AUTO_DISCOVER:
        plugin_registry.discover_and_load()
    plugin_registry.mount_routes(app)

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="pyweb-template - FastAPI + SQLAlchemy + Plugin 架构脚手架",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["framework"])
def health_check() -> dict[str, object]:
    """框架级健康检查（最简版）."""
    return {"status": "ok", "version": settings.APP_VERSION, "app": settings.APP_NAME}


@app.get("/api/plugins", tags=["framework"])
def list_plugins() -> dict[str, object]:
    """获取已加载插件列表."""
    from pyweb_template.core.plugin_registry import plugin_registry

    return {"plugins": plugin_registry.get_plugin_info_list()}


@app.get("/api/navigation", tags=["framework"])
def get_navigation() -> dict[str, object]:
    """汇总所有插件注册的侧边栏导航项."""
    from pyweb_template.core.plugin_registry import plugin_registry

    return {"navigation": plugin_registry.get_all_navigation()}


@app.get("/api/demos", tags=["framework"])
def get_demos() -> dict[str, object]:
    """列出内置 demo 入口的 HTTP 端点清单."""
    from pyweb_template.core.plugin_registry import plugin_registry
    from pyweb_template.plugins.base import NavItem

    plugins_nav: dict[str, list[dict[str, Any]]] = {}
    for plugin in plugin_registry._plugins.values():
        items = plugin.register_navigation()
        plugins_nav[plugin.name] = [i.to_dict() for i in items if isinstance(i, NavItem)]

    return {
        "cli": [
            "pywt serve           启动开发服务器",
            "pywt demo quickstart 串行跑最小 CRUD demo",
            "pywt demo plugins    列出所有已发现插件",
            "pywt info            打印版本/配置/运行环境",
        ],
        "http": [
            {"path": "/api/health", "desc": "框架健康检查"},
            {"path": "/api/plugins", "desc": "已加载插件列表"},
            {"path": "/api/navigation", "desc": "侧边栏导航汇总"},
            {"path": "/api/demos", "desc": "本端点"},
            {"path": "/api/v1/health/ping", "desc": "health 插件存活探针"},
            {"path": "/api/v1/crud-demo/users", "desc": "crud_demo 插件用户列表"},
        ],
        "plugins_navigation": plugins_nav,
    }
