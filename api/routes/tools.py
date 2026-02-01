"""
工具路由
"""
from typing import List
from fastapi import APIRouter, HTTPException

from api.schemas.common import ToolInfo, ToolInvokeRequest, ToolInvokeResponse

router = APIRouter()


@router.get("/tools", response_model=List[ToolInfo])
async def list_tools():
    """列出所有可用工具"""
    try:
        from core.tools.registry import ToolRegistry
        tools = ToolRegistry.list_tools()
        return [ToolInfo(**t) for t in tools]
    except ImportError:
        # 工具模块尚未实现
        return []


@router.post("/tools/invoke", response_model=ToolInvokeResponse)
async def invoke_tool(request: ToolInvokeRequest):
    """调用指定工具"""
    try:
        from core.tools.registry import ToolRegistry
        result = await ToolRegistry.execute(request.tool_name, request.parameters)
        
        return ToolInvokeResponse(
            tool_name=request.tool_name,
            success=result.success,
            data=result.data,
            error=result.error
        )
    except ImportError:
        raise HTTPException(status_code=501, detail="Tool system not implemented yet")
    except Exception as e:
        return ToolInvokeResponse(
            tool_name=request.tool_name,
            success=False,
            data=None,
            error=str(e)
        )
