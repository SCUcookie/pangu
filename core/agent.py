"""
Agent核心控制器 (AgentV3 科研版 - 工具增强与动态记忆)
整合记忆、工具、用户画像、推理引擎，协调完成用户请求
"""
import uuid
import time
import re
from typing import Any
from datetime import datetime

from .context import AgentContext, AgentDecision, ExecutionResult
from .prompts import build_system_prompt
from .memory.manager import MemoryManager
from .tools.registry import ToolRegistry
from .tools.builtin import register_builtin_tools
from .tools.advanced.python_sandbox import PythonSandboxTool
from .tools.advanced.sympy_solver import SympySolverTool

import sys
# 确保能够导入项目根目录的其他模块
sys.path.insert(0, '/opt/pangu/ldh/agentv2')

from difficulty_decision import DifficultyDecision
# form inference_engine import InferenceEngine  <-- 删除这一行
from data_loader import DataItem
from services.user_profile import UserProfileService
from services.session_manager import SessionManager
from api.schemas.chat import ChatRequest, ChatResponse, ChatMetadata

class AgentCore:
    """Agent核心控制器"""
    
    def __init__(self):
        # 延迟导入以解决循环依赖
        from inference_engine import InferenceEngine  # <-- 添加到这里

        self.inference_engine = InferenceEngine()
        self.difficulty_decision = DifficultyDecision()
        self.user_profile_service = UserProfileService()
        self.session_manager = SessionManager()
        
        # 注册所有工具 (包括基础工具和高级沙箱工具)
        register_builtin_tools()
        
        # 实例化并注册高阶工具
        python_tool = PythonSandboxTool(timeout=10)
        sympy_tool = SympySolverTool(timeout=10)
        ToolRegistry.register(python_tool)
        ToolRegistry.register(sympy_tool)
        
        self.max_react_steps = 4  # 限制最大工具调用循环次数

    # ... (其余代码保持不变)