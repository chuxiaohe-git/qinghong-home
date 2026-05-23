#!/bin/bash
# 轻鸿主页 - 一键启动脚本
# 用法: bash start.sh
# 自动启动后端 (Flask :5000) + 前端 (Vite :5173)

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ============================
# 自动探测 Python
# ============================
find_python() {
  if command -v python3 &>/dev/null; then echo "python3"; return 0; fi
  if command -v python &>/dev/null; then echo "python"; return 0; fi
  return 1
}

# ============================
# 自动探测 Node
# ============================
find_node() {
  if command -v node &>/dev/null; then
    dirname "$(command -v node)"; return 0
  fi
  return 1
}

# ============================
# 主流程
# ============================
echo "🧹 清理旧进程..."
for port in 5000 5173; do
  PID=$(lsof -ti :$port 2>/dev/null)
  if [ -n "$PID" ]; then
    kill "$PID" 2>/dev/null; sleep 1
    if lsof -ti :$port &>/dev/null; then
      kill -9 "$PID" 2>/dev/null; sleep 1
    fi
    echo "   端口 $port 旧进程已停止 (PID: $PID)"
  fi
done

PYTHON_CMD="$(find_python)"
if [ -z "$PYTHON_CMD" ]; then
  echo "❌ 找不到 Python，请先安装 Python 3"
  exit 1
fi
echo "✅ Python: $PYTHON_CMD"

NODE_DIR="$(find_node)"
if [ -z "$NODE_DIR" ]; then
  echo "❌ 找不到 Node.js，请先安装 Node.js"
  exit 1
fi
echo "✅ Node:   $NODE_DIR/node"
echo ""

# --- 安装依赖 ---
echo "📦 检查后端依赖..."
cd "$PROJECT_DIR/backend"
"$PYTHON_CMD" -m pip install -r requirements.txt -q 2>/dev/null
echo "📦 检查前端依赖..."
cd "$PROJECT_DIR"
if [ ! -d "node_modules" ]; then
  npm install --silent
fi

# --- 启动后端 ---
echo "🚀 启动后端 (Flask :5000)..."
cd "$PROJECT_DIR/backend"
"$PYTHON_CMD" app.py &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"
sleep 2

# --- 启动前端 ---
echo "🚀 启动前端 (Vite :5173)..."
export PATH="$NODE_DIR:$PATH"
cd "$PROJECT_DIR"
npx vite &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID"

echo ""
echo "═══════════════════════════════════════════"
echo "  ✅ 轻鸿主页 已启动！"
echo ""
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:5000"
echo ""
echo "  默认管理员: admin / admin123"
echo "═══════════════════════════════════════════"
echo ""
echo "按 Ctrl+C 停止所有服务"

cleanup() {
  echo ""; echo "🛑 正在停止服务..."
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
  echo "✅ 已停止"; exit 0
}
trap cleanup SIGINT SIGTERM
wait
