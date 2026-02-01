"""
工具注册中心
"""
from typing import Dict, List
from .base import BaseTool, ToolResult


class ToolRegistry:
    """工具注册中心"""
    
    _tools: Dict[str, BaseTool] = {}
    
    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """注册工具"""
        cls._tools[tool.name] = tool
    
    @classmethod
    def get(cls, name: str) -> BaseTool | None:
        """获取工具"""
        return cls._tools.get(name)
    
    @classmethod
    def list_tools(cls) -> List[dict]:
        """列出所有工具（供LLM使用）"""
        return [tool.get_schema_for_llm() for tool in cls._tools.values()]
    
    @classmethod
    def list_tool_names(cls) -> List[str]:
        """列出所有工具名称"""
        return list(cls._tools.keys())
    
    @classmethod
    async def execute(cls, name: str, params: dict) -> ToolResult:
        """执行指定工具"""
        tool = cls.get(name)
        if not tool:
            return ToolResult(success=False, data=None, error=f"Tool '{name}' not found")
        
        try:
            validated_params = tool.parameters_schema(**params)
            return await tool.execute(validated_params)
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))
    
    @classmethod
    def clear(cls) -> None:
        """清空所有工具（用于测试）"""
        cls._tools.clear()
