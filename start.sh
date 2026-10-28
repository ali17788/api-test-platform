#!/bin/bash
# AI驱动Web接口自动化测试平台 - 一键启动脚本（Windows / macOS / Linux）
set -e
cd "$(dirname "$0")"

PY=${PY:-python3}
PORT=${PORT:-8000}

echo "=============================================="
echo " AI驱动Web接口自动化测试平台 - 启动中"
echo "=============================================="

# 1. 检查/创建虚拟环境
if [ ! -d "venv" ]; then
  echo "[1/4] 创建 Python 虚拟环境..."
  $PY -m venv venv
fi
if [ -f "venv/bin/python" ]; then PYBIN="venv/bin/python"; else PYBIN="venv/Scripts/python"; fi

# 2. 安装依赖
echo "[2/4] 检查并安装依赖..."
$PYBIN -m pip install -q --upgrade pip >/dev/null 2>&1 || true
$PYBIN -m pip install -q -r requirements.txt

# 3. 构建前端（若尚未构建）
if [ ! -d "web" ] || [ -z "$(ls -A web 2>/dev/null)" ]; then
  echo "[3/4] 构建前端..."
  if command -v npm >/dev/null 2>&1; then
    (cd frontend && npm install --silent && npm run build)
  else
    echo "      未检测到 npm，将仅启动后端 API 服务（需 Node.js 16+ 以构建前端页面）"
  fi
else
  echo "[3/4] 前端构建产物已存在，跳过构建"
fi

# 4. 启动服务
echo "[4/4] 启动服务：http://127.0.0.1:${PORT}"
echo "----------------------------------------------"
echo " 演示账号：admin / admin123"
if [ -f "mock_api.py" ]; then
  $PYBIN mock_api.py >/dev/null 2>&1 &
  echo " 演示接口服务（Mock）：http://127.0.0.1:8099"
fi
echo "----------------------------------------------"
cd backend && PORT=$PORT $PYBIN app.py
