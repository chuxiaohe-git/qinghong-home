# ========================================
# 轻鸿主页 - 多阶段 Docker 构建
# ========================================

# ---- 阶段 1: 构建前端 ----
FROM node:22-alpine AS frontend-builder

WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --registry=https://registry.npmmirror.com
COPY vite.config.js index.html ./
COPY src/ src/
COPY public/ public/
RUN npm run build

# ---- 阶段 2: 运行后端 ----
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 安装后端依赖（使用国内镜像加速）
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt gunicorn

# 复制后端代码到 /app/backend/（保持和开发时一致的目录结构）
COPY backend/ backend/
# 构建好的前端到 /app/dist/
COPY --from=frontend-builder /build/dist/ dist/

# 创建必要目录
RUN mkdir -p backend/instance backend/uploads backend/backups

EXPOSE 5000

# 工作目录是 /app，但 gunicorn 的启动文件在 backend/ 下
# Flask 的 static_folder='../dist' 在 backend/ 中指向 /app/dist/
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--reload", "--chdir", "/app/backend", "app:app"]
