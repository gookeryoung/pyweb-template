"""pyweb_template Web 应用（FastAPI）."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="pyweb_template", description="Template for python web apps.")


@app.get("/")
def read_root() -> dict[str, str]:
    """根路径健康检查."""
    return {"status": "ok", "project": "pyweb_template"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("pyweb_template.app:app", host="0.0.0.0", port=8000, reload=True)
