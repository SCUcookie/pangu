"""
内置工具集合
"""
from .calculator import CalculatorTool
from .knowledge import KnowledgeTool
from .formula import FormulaLookupTool

__all__ = ["CalculatorTool", "KnowledgeTool", "FormulaLookupTool"]


def register_builtin_tools():
    """注册所有内置工具"""
    from ..registry import ToolRegistry
    
    ToolRegistry.register(CalculatorTool())
    ToolRegistry.register(KnowledgeTool())
    ToolRegistry.register(FormulaLookupTool())
