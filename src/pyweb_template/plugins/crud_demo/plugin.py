"""CRUD 示例插件.

提供最小可运行的内存 User CRUD，作为模板使用者实现业务插件的参考。
特点：
- 零数据库依赖（纯内存 dict），便于快速上手
- 标准 REST 风格路由（GET/POST/PUT/DELETE /users）
- 自动注册侧边栏导航项
"""

from __future__ import annotations

import datetime as dt
import threading
from dataclasses import dataclass
from typing import override

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from pyweb_template.plugins.base import NavItem, PluginBase

# ── 内存数据层（生产请替换为 SQLAlchemy model + Repository）─────────


@dataclass
class _UserRecord:
    id: int
    username: str
    email: str
    role: str
    created_at: str
    updated_at: str


class _InMemoryUserStore:
    """线程安全的 User 内存仓库（仅做 demo）."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._users: dict[int, _UserRecord] = {}
        self._seq = 1
        self._seed()

    def _seed(self) -> None:
        now = dt.datetime.now(dt.UTC).isoformat()
        self.create("admin", "admin@example.com", "admin", now)
        self.create("demo", "demo@example.com", "user", now)

    def create(self, username: str, email: str, role: str, created_at: str) -> _UserRecord:
        with self._lock:
            record = _UserRecord(
                id=self._seq,
                username=username,
                email=email,
                role=role,
                created_at=created_at,
                updated_at=created_at,
            )
            self._seq += 1
            self._users[record.id] = record
            return record

    def get(self, user_id: int) -> _UserRecord | None:
        with self._lock:
            return self._users.get(user_id)

    def list(self, offset: int = 0, limit: int = 50) -> tuple[list[_UserRecord], int]:
        with self._lock:
            all_items = list(self._users.values())
            total = len(all_items)
            page = all_items[offset : offset + limit]
            return page, total

    def update(self, user_id: int, username: str | None, email: str | None, role: str | None) -> _UserRecord | None:
        with self._lock:
            record = self._users.get(user_id)
            if record is None:
                return None
            now = dt.datetime.now(dt.UTC).isoformat()
            if username is not None:
                record.username = username
            if email is not None:
                record.email = email
            if role is not None:
                record.role = role
            record.updated_at = now
            return record

    def delete(self, user_id: int) -> bool:
        with self._lock:
            return self._users.pop(user_id, None) is not None


_store = _InMemoryUserStore()


# ── Pydantic Schema ──────────────────────────────────────


class UserCreate(BaseModel):
    """创建用户请求体."""

    username: str = Field(..., min_length=2, max_length=32, description="用户名")
    email: str = Field(..., description="邮箱地址")
    role: str = Field("user", description="角色（admin/user/guest）")


class UserUpdate(BaseModel):
    """更新用户请求体（所有字段可选）."""

    model_config = ConfigDict(extra="ignore")

    username: str | None = Field(default=None, min_length=2, max_length=32)
    email: str | None = None
    role: str | None = None


class UserResponse(BaseModel):
    """用户响应体."""

    id: int
    username: str
    email: str
    role: str
    created_at: str
    updated_at: str


class UserListResponse(BaseModel):
    """列表响应（带分页元信息）."""

    items: list[UserResponse]
    total: int
    offset: int
    limit: int


def _record_to_response(record: _UserRecord) -> UserResponse:
    return UserResponse(
        id=record.id,
        username=record.username,
        email=record.email,
        role=record.role,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


# ── 插件类 ──────────────────────────────────────────────


class CrudDemoPlugin(PluginBase):
    """CRUD 示例插件（内存 User 仓库）."""

    name = "crud-demo"
    version = "0.1.0"
    description = "内置最小 User CRUD，演示 PluginBase 用法"
    icon = "UserOutlined"

    @override
    def register_routes(self, router: APIRouter) -> None:
        @router.get("/users", response_model=UserListResponse)
        def list_users(
            offset: int = Query(0, ge=0, description="偏移量"),
            limit: int = Query(50, ge=1, le=200, description="每页条数"),
        ) -> UserListResponse:
            """分页查询用户列表."""
            items, total = _store.list(offset=offset, limit=limit)
            return UserListResponse(
                items=[_record_to_response(r) for r in items],
                total=total,
                offset=offset,
                limit=limit,
            )

        @router.get("/users/{user_id}", response_model=UserResponse)
        def get_user(user_id: int) -> UserResponse:
            """按 ID 查询单个用户."""
            record = _store.get(user_id)
            if record is None:
                raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
            return _record_to_response(record)

        @router.post("/users", response_model=UserResponse, status_code=201)
        def create_user(payload: UserCreate) -> UserResponse:
            """创建新用户."""
            now = dt.datetime.now(dt.UTC).isoformat()
            record = _store.create(payload.username, payload.email, payload.role, now)
            return _record_to_response(record)

        @router.put("/users/{user_id}", response_model=UserResponse)
        def update_user(user_id: int, payload: UserUpdate) -> UserResponse:
            """更新用户信息."""
            record = _store.update(user_id, payload.username, payload.email, payload.role)
            if record is None:
                raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
            return _record_to_response(record)

        @router.delete("/users/{user_id}", status_code=204)
        def delete_user(user_id: int) -> None:
            """删除用户."""
            if not _store.delete(user_id):
                raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")

    @override
    def register_navigation(self) -> list[NavItem]:
        return [
            NavItem(
                key="crud-demo",
                label="CRUD 示例",
                icon="UserOutlined",
                path="/crud-demo/users",
            )
        ]
