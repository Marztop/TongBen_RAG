#!/bin/bash

set -e

echo "🚀 启动 Mineru 代理服务..."

# 检查必需的配置
if [ -z "$MINERU_API_KEY" ]; then
    echo "❌ 错误: MINERU_API_KEY 未设置"
    echo "请运行: export MINERU_API_KEY=your_api_key_here"
    exit 1
fi

# 获取脚本所在的目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✅ 虚拟环境创建完成"
else
    source venv/bin/activate
fi

# 启动服务
PORT=${PROXY_PORT:-5000}
HOST=${PROXY_HOST:-0.0.0.0}

echo "✅ 服务启动在 http://${HOST}:${PORT}"
echo ""
echo "📝 日志信息："
echo "======================================"
echo ""

python app.py
