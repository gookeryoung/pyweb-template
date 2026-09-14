"""Alembic 迁移环境配置.

通过 settings.DATABASE_URL 获取数据库连接串，
通过 target_metadata 收集所有插件注册的 SQLAlchemy Model。
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from pyweb_template.core.config import settings
from pyweb_template.core.plugin_registry import plugin_registry
from pyweb_template.models.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 使用项目配置中的 DATABASE_URL（覆盖 alembic.ini 中的占位值）
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# 确保所有插件已加载（触发 register_models）
if settings.PLUGINS_AUTO_DISCOVER:
    plugin_registry.discover_and_load()

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式迁移（不需要真实 DB 连接，只生成 SQL）."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式迁移（真实 DB 连接）."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
