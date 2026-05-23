#!/bin/bash
# 轻鸿主页 - 一键启动脚本
# 用法: bash start.sh
# 自动启动后端 (Flask :5000) + 前端 (Vite :3000)

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ============================
# 自动探测 Python 路径
# ============================
find_python() {
  local candidates=(
    "/opt/miniforge3/envs/works/bin/python3"
    "/opt/miniforge3/envs/works/bin/python"
    "/opt/miniconda3/envs/works/bin/python3"
    "/opt/miniconda3/envs/works/bin/python"
  )
  if command -v conda &>/dev/null; then
    local conda_base
    conda_base="$(conda info --base 2>/dev/null)"
    if [ -n "$conda_base" ]; then
      candidates+=("$conda_base/envs/works/bin/python3")
      candidates+=("$conda_base/envs/works/bin/python")
    fi
  fi
  if [ -n "$CONDA_PREFIX" ]; then
    local envs_dir
    envs_dir="$(dirname "$CONDA_PREFIX")"
    candidates+=("$envs_dir/works/bin/python3")
    candidates+=("$envs_dir/works/bin/python")
  fi
  for p in "${candidates[@]}"; do
    if [ -x "$p" ]; then echo "$p"; return 0; fi
  done
  if command -v python3 &>/dev/null; then echo "python3"; return 0; fi
  if command -v python &>/dev/null; then echo "python"; return 0; fi
  return 1
}

# ============================
# 自动探测 Node.js 路径
# ============================
find_node_dir() {
  if command -v node &>/dev/null; then
    dirname "$(command -v node)"; return 0
  fi
  local candidates=(
    "/opt/homebrew/bin"
    "/usr/local/bin"
    "$HOME/.workbuddy/binaries/node/versions/25.8.1/bin"
    "$HOME/.workbuddy/binaries/node/versions/22.12.0/bin"
  )
  for d in "${candidates[@]}"; do
    if [ -x "$d/node" ]; then echo "$d"; return 0; fi
  done
  return 1
}

# ============================
# 主流程
# ============================
echo "🧹 清理旧进程..."
for port in 5000 3000; do
  PID=$(lsof -ti :$port 2>/dev/null)
  if [ -n "$PID" ]; then
    kill "$PID" 2>/dev/null
    sleep 1
    # 如果还没释放，强杀
    if lsof -ti :$port &>/dev/null; then
      kill -9 "$PID" 2>/dev/null
      sleep 1
    fi
    echo "   端口 $port 旧进程已停止 (PID: $PID)"
  fi
done

PYTHON_CMD="$(find_python)"
if [ -z "$PYTHON_CMD" ]; then
  echo "❌ 找不到 Python（需要 conda env: works），请检查 conda 环境"
  exit 1
fi
echo "✅ Python: $PYTHON_CMD"

NODE_DIR="$(find_node_dir)"
if [ -z "$NODE_DIR" ]; then
  echo "❌ 找不到 Node.js，请检查安装"
  exit 1
fi
echo "✅ Node:   $NODE_DIR/node"
echo ""

# --- 启动后端 ---
echo "🚀 启动后端 (Flask :5000)..."
cd "$PROJECT_DIR/backend"
"$PYTHON_CMD" app.py &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"
sleep 3

# --- 启动前端 ---
echo "🚀 启动前端 (Vite :3000)..."
export PATH="$NODE_DIR:$PATH"
cd "$PROJECT_DIR"
"$NODE_DIR/npm" run dev &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID"

echo ""
echo "═══════════════════════════════════════════"
echo "  ✅ 轻鸿主页 已启动！"
echo ""
echo "  前端:  http://localhost:3000"
echo "  后端:  http://localhost:5000"
echo ""
echo "  默认管理员: admin / admin123"
echo "═══════════════════════════════════════════"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获退出信号，清理子进程
cleanup() {
  echo ""
  echo "🛑 正在停止服务..."
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
  echo "✅ 已停止"
  exit 0
}
trap cleanup SIGINT SIGTERM

wait
