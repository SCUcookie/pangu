"""
通用Schema定义
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ToolInfo(BaseModel):
    """工具信息"""
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolInvokeRequest(BaseModel):
    """工具调用请求"""
    tool_name: str
    parameters: Dict[str, Any] = {}


class ToolInvokeResponse(BaseModel):
    """工具调用响应"""
    tool_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    code: str
    detail: Optional[str] = None
