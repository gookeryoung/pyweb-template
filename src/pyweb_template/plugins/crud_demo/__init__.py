"""crud_demo 插件包.

演示模板内置的最小 CRUD 功能：
- 一个内存 User 仓库（不依赖 SQLAlchemy，降低模板复杂度）
- 完整的增删改查 + 列表分页 API
- 在侧边栏注册菜单项

模板使用者可参照此插件实现自己的业务插件。
"""

from __future__ import annotations

from pyweb_template.plugins.crud_demo.plugin import CrudDemoPlugin

__all__ = ["CrudDemoPlugin"]
