"""
工具基类定义
"""
from abc import ABC, abstractmethod
from typing import Any, Type
from pydantic import BaseModel


class ToolParameter(BaseModel):
    """工具参数基类"""
    pass


class ToolResult(BaseModel):
    """工具返回结果"""
    success: bool
    data: Any = None
    error: str | None = None


class BaseTool(ABC):
    """工具基类"""
    
    name: str = ""
    description: str = ""
    parameters_schema: Type[ToolParameter] = ToolParameter
    
    @abstractmethod
    async def execute(self, params: ToolParameter) -> ToolResult:
        """执行工具"""
        pass
    
    def get_schema_for_llm(self) -> dict:
        """获取供LLM使用的工具描述"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters_schema.model_json_schema()
        }
