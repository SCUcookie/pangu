"""
SymPy 符号计算工具 (科研版)
专门用于大模型的微积分、代数方程求解。
"""
import io
import contextlib
import multiprocessing
import traceback
from typing import Dict, Any

def _run_sympy(code: str, return_dict: dict):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            import sympy
            from sympy import symbols, Eq, solve, expand, factor, limit, diff, integrate, oo, pi, I, E
            
            # 提供基础的 sympy 环境变量
            safe_globals = {
                "__builtins__": {"print": print, "int": int, "float": float, "str": str, "list": list, "dict": dict},
                "sympy": sympy,
                "symbols": symbols, "Eq": Eq, "solve": solve, "expand": expand, 
                "factor": factor, "limit": limit, "diff": diff, "integrate": integrate,
                "oo": oo, "pi": pi, "I": I, "E": E
            }
            exec(code, safe_globals, {})
            return_dict['success'] = True
            return_dict['output'] = stdout.getvalue()
        except Exception as e:
            return_dict['success'] = False
            return_dict['error'] = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc(limit=1)}"
            return_dict['output'] = stdout.getvalue() + "\n" + stderr.getvalue()

class SympySolverTool:
    name = "sympy_solver"
    description = "执行 sympy 代码进行符号计算。环境已预导入 sympy, symbols, Eq, solve, expand, factor, limit, diff, integrate 等常用函数。输入必须是有效的 Python 代码并使用 print() 输出结果。"
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        
    async def execute(self, code: str) -> Dict[str, Any]:
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        
        if code.startswith("```python"):
            code = code[len("```python"):].strip()
        elif code.startswith("```"):
            code = code[len("```"):].strip()
        if code.endswith("```"):
            code = code[:-3].strip()
            
        p = multiprocessing.Process(target=_run_sympy, args=(code, return_dict))
        p.start()
        p.join(self.timeout)
        
        if p.is_alive():
            p.terminate()
            p.join()
            return {"success": False, "data": "Timeout: Execution exceeded the time limit."}
            
        if return_dict.get('success'):
            output = return_dict.get('output', '').strip()
            if not output:
                output = "Code executed successfully but no output was printed."
            return {"success": True, "data": output}
        else:
            return {"success": False, "data": return_dict.get('error', 'Unknown Error')}
