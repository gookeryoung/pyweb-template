"""crud_demo 插件集成测试."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from pyweb_template.app import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_seed_data_present(client: TestClient) -> None:
    """启动后应有两条种子用户 (admin / demo)."""
    r = client.get("/api/v1/crud-demo/users")
    assert r.status_code == 200
    assert r.json()["total"] >= 2


def test_create_user(client: TestClient) -> None:
    r = client.post(
        "/api/v1/crud-demo/users",
        json={"username": "alice", "email": "alice@x.com", "role": "user"},
    )
    assert r.status_code == 201
    d = r.json()
    assert d["username"] == "alice"
    assert "id" in d
    return  # 不返回，pytest 里直接断言


def test_get_user(client: TestClient) -> None:
    # 先创建一条
    r = client.post(
        "/api/v1/crud-demo/users",
        json={"username": "bob", "email": "bob@x.com", "role": "user"},
    )
    uid = r.json()["id"]
    # 再取
    r2 = client.get(f"/api/v1/crud-demo/users/{uid}")
    assert r2.status_code == 200
    assert r2.json()["username"] == "bob"


def test_get_user_not_found(client: TestClient) -> None:
    r = client.get("/api/v1/crud-demo/users/999999")
    assert r.status_code == 404


def test_update_user(client: TestClient) -> None:
    r = client.post(
        "/api/v1/crud-demo/users",
        json={"username": "carol", "email": "carol@x.com", "role": "user"},
    )
    uid = r.json()["id"]
    r2 = client.put(f"/api/v1/crud-demo/users/{uid}", json={"role": "admin"})
    assert r2.status_code == 200
    assert r2.json()["role"] == "admin"


def test_delete_user(client: TestClient) -> None:
    r = client.post(
        "/api/v1/crud-demo/users",
        json={"username": "dave", "email": "dave@x.com"},
    )
    uid = r.json()["id"]
    r2 = client.delete(f"/api/v1/crud-demo/users/{uid}")
    assert r2.status_code == 204
    # 删除后应 404
    r3 = client.get(f"/api/v1/crud-demo/users/{uid}")
    assert r3.status_code == 404


def test_list_pagination(client: TestClient) -> None:
    r = client.get("/api/v1/crud-demo/users?offset=0&limit=1")
    assert r.status_code == 200
    data = r.json()
    assert data["limit"] == 1
    assert len(data["items"]) <= 1
