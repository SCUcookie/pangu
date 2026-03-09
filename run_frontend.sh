#!/bin/bash
# 启动前端应用

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查是否安装了streamlit
if ! command -v streamlit &> /dev/null; then
    echo "Streamlit is not installed. Installing dependencies..."
    pip install -r requirements.txt
fi

echo "Starting Streamlit frontend..."
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
