# ────────────────────────────────────────────────────────────────────
# pyweb_template 多阶段 Dockerfile
#
# 阶段：
#   frontend  — Node.js 构建前端 Vite 产物
#   app       — Python + uv + FastAPI 后端（含前端静态）
#   web       — nginx 反代 + SPA fallback（与 docker-compose 配套）
#
# 构建 & 运行（源码形态）：
#   docker compose up -d --build
#
# 单阶段直出（app，内置前端静态文件）：
#   docker build --target app -t pywt-app .
#   docker run -p 8000:8000 pywt-app
# ────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────
# 阶段 1：frontend — 构建前端
# ────────────────────────────────────────────────────────────────────
FROM docker.m.daocloud.io/node:20-alpine AS frontend

WORKDIR /app

# 利用层缓存：先拷贝依赖描述文件
COPY frontend/package.json frontend/package-lock.json ./
RUN npm config set registry https://registry.npmmirror.com \
    && npm ci --no-audit --no-fund

# 拷贝源码并构建
COPY frontend/ ./
RUN npm run build \
    && echo "Frontend built: $(ls -la dist/ | head -5)"


# ────────────────────────────────────────────────────────────────────
# 阶段 2：app — FastAPI 后端 + 内置前端静态
# ────────────────────────────────────────────────────────────────────
FROM docker.m.daocloud.io/python:3.14-slim AS app

# ── 国内镜像源 ──
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn
ENV UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV UV_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# 环境变量：非交互 + 路径配置
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/uv-cache \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 安装系统依赖 + uv（国内镜像）
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null; \
    apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv -i https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app

# 拷贝 Python 项目（利用层缓存：先拷贝依赖描述）
COPY pyproject.toml uv.lock* README.md ./
COPY alembic.ini alembic/ ./alembic/
COPY src/ ./src/

# 同步 Python 依赖（不装项目本身，等前端产物到位后再装）
RUN uv sync --frozen --no-install-project --extra dev || uv sync --no-install-project

# 从 frontend 阶段拷贝 Vite 构建产物到后端 static 目录
COPY --from=frontend /app/dist/ ./src/pyweb_template/static/

# 安装项目本身（此时 static 目录已存在，hatchling force-include 会自动打包）
RUN uv sync --frozen --extra dev || uv sync --extra dev

# 创建数据卷目录（SQLite / 上传文件）
RUN mkdir -p /data /uploads

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
    CMD curl -fsS http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "pyweb_template.app:app", "--host", "0.0.0.0", "--port", "8000"]


# ────────────────────────────────────────────────────────────────────
# 阶段 3：web — nginx 反代（SPA fallback + /api/* → app）
# ────────────────────────────────────────────────────────────────────
FROM docker.m.daocloud.io/nginx:1.27-alpine AS web

# 拷贝 nginx 配置
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
