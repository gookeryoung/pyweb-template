"""框架级 HTTP 路由测试."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from pyweb_template.app import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "ok"
    assert d["app"] == "pyweb_template"


def test_plugins_endpoint(client: TestClient) -> None:
    r = client.get("/api/plugins")
    assert r.status_code == 200
    names = {p["name"] for p in r.json()["plugins"]}
    assert "health" in names
    assert "crud-demo" in names


def test_navigation_endpoint(client: TestClient) -> None:
    r = client.get("/api/navigation")
    assert r.status_code == 200
    nav = r.json()["navigation"]
    keys = {n["key"] for n in nav}
    assert "crud-demo" in keys


def test_demos_endpoint(client: TestClient) -> None:
    r = client.get("/api/demos")
    assert r.status_code == 200
    d = r.json()
    assert "cli" in d
    assert "http" in d
    assert len(d["http"]) >= 4
