#!/bin/bash
# ============================================================
#  云端部署启动入口（Render / Railway / 任意 PaaS）
#  说明：前端已预构建在 web/ 中并随仓库提交，运行时无需 Node.js；
#        仅启动 FastAPI 后端，由它托管静态页面与 API。
#        端口读取环境变量 PORT（云端自动注入），绑定 0.0.0.0。
# ============================================================
set -e
cd "$(dirname "$0")"

PORT="${PORT:-8000}"
PY="${PY:-python3}"

# 若构建环境把依赖装进了 venv，则优先使用
if [ -f "venv/bin/python" ]; then
  PYBIN="venv/bin/python"
elif [ -f "venv/Scripts/python.exe" ]; then
  PYBIN="venv/Scripts/python.exe"
else
  PYBIN="$PY"
fi

echo "=============================================="
echo " AI驱动Web接口自动化测试平台 - 云端启动"
echo " 监听 0.0.0.0:${PORT}"
echo " 演示账号：admin / admin123"
echo "=============================================="

cd backend
exec env PORT="$PORT" "$PYBIN" app.py
