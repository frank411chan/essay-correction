#!/bin/bash

# 作文批改系统一键启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "      作文批改系统启动中..."
echo "========================================"

# 安装后端依赖
echo "[1/3] 检查并安装后端依赖..."
cd backend
if [ ! -d "venv" ]; then
    echo "创建后端虚拟环境..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
cd "$SCRIPT_DIR"

# 安装前端依赖
echo "[2/3] 检查并安装前端依赖..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi
cd "$SCRIPT_DIR"

# 启动后端
echo "[3/3] 启动服务..."
python3 start-backend.py
python3 start-frontend.py

echo ""
echo "========================================"
echo "  启动命令已执行！"
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:8001"
echo "  API 文档: http://localhost:8001/docs"
echo "========================================"
echo ""
echo "如果服务未立即响应，请等待 3-5 秒后刷新浏览器。"
