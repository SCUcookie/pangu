"""
Python代码执行沙箱 (科研版)
用于处理大模型无法直接计算的复杂数学、物理、概率运算。
"""
import io
import contextlib
import multiprocessing
import traceback
from typing import Dict, Any

def _run_code(code: str, return_dict: dict):
    """在子进程中运行代码以限制时间和资源"""
    stdout = io.StringIO()
    stderr = io.StringIO()
    
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            # 限制可用内置函数，防范危险操作
            safe_globals = {
                "__builtins__": {
                    "print": print, "range": range, "len": len, "sum": sum,
                    "abs": abs, "min": min, "max": max, "round": round,
                    "int": int, "float": float, "str": str, "list": list, "dict": dict,
                    "set": set, "tuple": tuple, "bool": bool, "enumerate": enumerate,
                    "zip": zip, "map": map, "filter": filter, "any": any, "all": all
                },
                "math": __import__("math"),
                "cmath": __import__("cmath"),
                "random": __import__("random"),
                "itertools": __import__("itertools"),
                "collections": __import__("collections")
            }
            exec(code, safe_globals, {})
            return_dict['success'] = True
            return_dict['output'] = stdout.getvalue()
        except Exception as e:
            return_dict['success'] = False
            return_dict['error'] = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc(limit=1)}"
            return_dict['output'] = stdout.getvalue() + "\n" + stderr.getvalue()

class PythonSandboxTool:
    name = "python_sandbox"
    description = "执行Python代码进行复杂计算。输入应为包含 print 语句的纯Python代码字符串。该工具可解决复杂的数学、物理运算和统计问题。"
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        
    async def execute(self, code: str) -> Dict[str, Any]:
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        
        # 清理代码块中的 markdown 标记
        if code.startswith("```python"):
            code = code[len("```python"):].strip()
        elif code.startswith("```"):
            code = code[len("```"):].strip()
        if code.endswith("```"):
            code = code[:-3].strip()
            
        p = multiprocessing.Process(target=_run_code, args=(code, return_dict))
        p.start()
        p.join(self.timeout)
        
        if p.is_alive():
            p.terminate()
            p.join()
            return {"success": False, "data": "Timeout: Execution exceeded the time limit."}
            
        if return_dict.get('success'):
            output = return_dict.get('output', '').strip()
            if not output:
                output = "Code executed successfully but no output was printed. Use print() to output results."
            return {"success": True, "data": output}
        else:
            return {"success": False, "data": return_dict.get('error', 'Unknown Error')}
