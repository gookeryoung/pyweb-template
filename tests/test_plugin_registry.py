"""core.plugin_registry 测试."""

from __future__ import annotations

from fastapi import FastAPI

from pyweb_template.core.plugin_registry import PluginRegistry
from pyweb_template.plugins.base import AppItem, NavItem, PluginBase


def test_empty_registry() -> None:
    """初始状态应无插件."""
    r = PluginRegistry()
    assert len(r) == 0
    assert r.get_plugin_info_list() == []
    assert r.get_all_navigation() == []
    assert r.get_all_apps() == []


def test_register_and_get() -> None:
    """注册后应能通过 name 获取."""

    class FakePlugin(PluginBase):
        name = "fake"
        description = "test"

        def register_routes(self, router) -> None:  # noqa: ANN001
            pass

    r = PluginRegistry()
    r.register(FakePlugin())
    assert r.get_plugin("fake") is not None
    assert len(r) == 1
    info = r.get_plugin_info_list()[0]
    assert info["name"] == "fake"
    assert info["description"] == "test"


def test_duplicate_register_skipped() -> None:
    """同名插件重复注册应被跳过."""

    class FakePlugin(PluginBase):
        name = "dup"

        def register_routes(self, router) -> None:  # noqa: ANN001
            pass

    r = PluginRegistry()
    r.register(FakePlugin())
    r.register(FakePlugin())  # 同名
    assert len(r) == 1


def test_discover_loads_builtin_plugins() -> None:
    """discover_and_load 应能找到 health + crud_demo."""
    # 用新实例避免全局单例影响
    from pyweb_template.core.plugin_registry import PluginRegistry as _PR

    r = _PR()
    r.discover_and_load()
    names = {p["name"] for p in r.get_plugin_info_list()}
    assert "health" in names
    assert "crud-demo" in names


def test_mount_routes_is_idempotent() -> None:
    """mount_routes 应幂等，不重复挂载."""

    class FakePlugin(PluginBase):
        name = "idempotent-test"

        def register_routes(self, router) -> None:  # noqa: ANN001
            @router.get("/ping")
            def ping() -> str:
                return "ok"

    r = PluginRegistry()
    r.register(FakePlugin())

    app = FastAPI()
    r.mount_routes(app)
    n_first = len(app.routes)
    r.mount_routes(app)  # 再调一次
    n_second = len(app.routes)
    assert n_first == n_second


def test_get_all_navigation_collects() -> None:
    """应能从插件收集导航项."""

    class NavPlugin(PluginBase):
        name = "nav-test"

        def register_routes(self, router) -> None:  # noqa: ANN001
            pass

        def register_navigation(self) -> list[NavItem]:
            return [NavItem(key="a", label="A", path="/a")]

    r = PluginRegistry()
    r.register(NavPlugin())
    nav = r.get_all_navigation()
    assert len(nav) == 1
    assert nav[0]["key"] == "a"
    assert nav[0]["path"] == "/a"


def test_get_all_apps_collects() -> None:
    """应能从插件收集 APP 入口."""

    class AppPlugin(PluginBase):
        name = "app-test"

        def register_routes(self, router) -> None:  # noqa: ANN001
            pass

        def register_apps(self) -> list[AppItem]:
            return [AppItem(key="x", label="X", path="/x")]

    r = PluginRegistry()
    r.register(AppPlugin())
    apps = r.get_all_apps()
    assert len(apps) == 1
    assert apps[0]["key"] == "x"
