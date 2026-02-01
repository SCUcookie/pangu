"""
健康检查路由
"""
from fastapi import APIRouter
import requests

from config import VLLM_MODELS_URL

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查"""
    # 检查vLLM服务状态
    vllm_status = "unknown"
    try:
        resp = requests.get(VLLM_MODELS_URL, timeout=5)
        vllm_status = "healthy" if resp.status_code == 200 else "unhealthy"
    except Exception:
        vllm_status = "unreachable"
    
    return {
        "status": "healthy",
        "components": {
            "api": "healthy",
            "vllm": vllm_status
        }
    }
