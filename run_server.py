#!/usr/bin/env python3
"""
Agent API服务启动脚本
"""
import uvicorn
from config import API_HOST, API_PORT


def main():
    """启动API服务"""
    print("="*60)
    print("盘古教育Agent API服务")
    print("="*60)
    print(f"启动地址: http://{API_HOST}:{API_PORT}")
    print(f"API文档: http://{API_HOST}:{API_PORT}/docs")
    print("="*60)
    
    uvicorn.run(
        "api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,  # 开发模式启用热重载
        log_level="info"
    )


if __name__ == "__main__":
    main()
