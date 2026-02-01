"""
计算器工具
"""
import math
import re
from ..base import BaseTool, ToolParameter, ToolResult


class CalculatorParams(ToolParameter):
    """计算器参数"""
    expression: str  # 数学表达式


class CalculatorTool(BaseTool):
    """数学计算工具"""
    
    name = "calculator"
    description = "执行数学计算，支持基本运算(+,-,*,/,**,%)和常用数学函数(sin,cos,tan,sqrt,log,exp等)"
    parameters_schema = CalculatorParams
    
    # 允许的安全函数
    SAFE_FUNCTIONS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'pow': pow,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'log': math.log,
        'log10': math.log10,
        'log2': math.log2,
        'exp': math.exp,
        'floor': math.floor,
        'ceil': math.ceil,
        'pi': math.pi,
        'e': math.e,
    }
    
    async def execute(self, params: CalculatorParams) -> ToolResult:
        """执行计算"""
        expression = params.expression.strip()
        
        # 安全检查：只允许数字、运算符和白名单函数
        if not self._is_safe_expression(expression):
            return ToolResult(
                success=False,
                error="不安全的表达式，只允许数学运算和基本函数"
            )
        
        try:
            # 使用受限环境执行
            result = eval(expression, {"__builtins__": {}}, self.SAFE_FUNCTIONS)
            return ToolResult(success=True, data=result)
        except ZeroDivisionError:
            return ToolResult(success=False, error="除零错误")
        except Exception as e:
            return ToolResult(success=False, error=f"计算错误: {str(e)}")
    
    def _is_safe_expression(self, expr: str) -> bool:
        """检查表达式是否安全"""
        # 允许的字符：数字、运算符、括号、小数点、空格、函数名
        allowed_pattern = r'^[\d\s\+\-\*\/\%\^\(\)\.\,a-zA-Z_]+$'
        if not re.match(allowed_pattern, expr):
            return False
        
        # 检查是否包含危险关键字
        dangerous = ['import', 'exec', 'eval', 'open', 'file', '__', 'os', 'sys']
        expr_lower = expr.lower()
        for word in dangerous:
            if word in expr_lower:
                return False
        
        return True
