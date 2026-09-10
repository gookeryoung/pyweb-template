"""进程内 CRUD demo 逻辑.

与 runner.demo_quickstart 共享 TestClient 代码，但以纯函数形式暴露，
便于 pytest 单元测试独立调用（不依赖 argparse）。
"""

from __future__ import annotations

from typing import Any


def run_crud_demo() -> dict[str, Any]:
    """完整跑一遍最小 CRUD 流程，返回步骤结果字典.

    Returns:
        每个步骤的结果汇总，便于调用方断言或打印。
        所有步骤均成功时 success=True。
    """
    from fastapi.testclient import TestClient

    from pyweb_template.app import app

    results: list[dict[str, Any]] = []
    success = True

    with TestClient(app) as client:
        # 1. 健康检查
        r = client.get("/api/health")
        ok = r.status_code == 200 and r.json().get("status") == "ok"
        results.append({"step": "health", "ok": ok, "status": r.status_code})
        success &= ok

        # 2. 创建
        r = client.post(
            "/api/v1/crud-demo/users",
            json={"username": "cli-demo", "email": "cli@pywt.local", "role": "user"},
        )
        ok = r.status_code == 201
        user_id = r.json()["id"] if ok else None
        results.append({"step": "create", "ok": ok, "user_id": user_id})
        success &= ok
        if not ok or user_id is None:
            return {"success": False, "results": results}

        # 3. 列表
        r = client.get("/api/v1/crud-demo/users")
        ok = r.status_code == 200 and len(r.json()["items"]) >= 2  # 2 条 seed + 1 新建
        results.append({"step": "list", "ok": ok, "count": r.json()["items"] if r.status_code == 200 else None})
        success &= ok

        # 4. 单个
        r = client.get(f"/api/v1/crud-demo/users/{user_id}")
        ok = r.status_code == 200 and r.json()["username"] == "cli-demo"
        results.append({"step": "get", "ok": ok})
        success &= ok

        # 5. 更新
        r = client.put(f"/api/v1/crud-demo/users/{user_id}", json={"role": "admin"})
        ok = r.status_code == 200 and r.json()["role"] == "admin"
        results.append({"step": "update", "ok": ok})
        success &= ok

        # 6. 删除
        r = client.delete(f"/api/v1/crud-demo/users/{user_id}")
        ok = r.status_code == 204
        results.append({"step": "delete", "ok": ok})
        success &= ok

        # 7. 插件
        r = client.get("/api/plugins")
        ok = r.status_code == 200 and len(r.json()["plugins"]) >= 2
        results.append({"step": "plugins", "ok": ok, "count": len(r.json()["plugins"]) if r.status_code == 200 else 0})
        success &= ok

    return {"success": success, "results": results}
