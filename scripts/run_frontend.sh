#!/bin/bash
# 启动前端应用
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT"

# 检查是否安装了streamlit
if ! command -v streamlit &> /dev/null; then
    echo "Streamlit is not installed. Installing dependencies..."
    pip install -r "$PROJECT_ROOT/requirements.txt"
fi

echo "Starting Streamlit frontend..."
streamlit run "$PROJECT_ROOT/frontend/app.py" --server.port 8501 --server.address 0.0.0.0
