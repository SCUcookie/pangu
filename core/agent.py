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
from inference_engine import InferenceEngine
from data_loader import DataItem
from services.user_profile import UserProfileService
from services.session_manager import SessionManager
from api.schemas.chat import ChatRequest, ChatResponse, ChatMetadata

class AgentCore:
    """Agent核心控制器"""
    
    def __init__(self):
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
    
    async def process(self, request: ChatRequest, db_session) -> ChatResponse:
        """处理用户请求的主入口"""
        start_time = time.time()
        
        # 1. 初始化上下文
        context = await self._init_context(request, db_session)
        
        # 2. 决策 (快/慢思考)
        decision = await self._make_decision(context)
        
        # 3. 执行
        if decision.thinking_mode in ["slow", "both"]:
            # 科研改动点二：启动 ReAct 循环
            result = await self._execute_react_loop(context, decision)
        else:
            # 快思考直接推理
            result = await self._execute_fast(context, decision)
        
        # 4. 后处理
        response = await self._post_process(context, result, start_time, db_session)
        return response
    
    async def _init_context(self, request: ChatRequest, db_session) -> AgentContext:
        """初始化上下文，提取动态记忆"""
        # 获取或创建会话
        session = None
        if request.session_id:
            session = await self.session_manager.get_session(db_session, request.session_id)
        if not session:
            session = await self.session_manager.create_session(
                db_session, request.user_id,
                task_type=request.task_type,
                subject=request.context.subject if request.context else None
            )
        
        # 获取用户画像
        user_profile = await self.user_profile_service.get_profile(db_session, request.user_id)
        if not user_profile:
            user_profile = await self.user_profile_service.create_profile(db_session, request.user_id)
            
        # 科研改动点一：动态记忆提取
        subject = request.context.subject if request.context else None
        dynamic_memory = await self.user_profile_service.get_active_memory_prompt(
            db_session, request.user_id, current_subject=subject
        )
        
        # 构建记忆管理器
        memory = MemoryManager(request.user_id, session.session_id)
        messages = await self.session_manager.get_messages(db_session, session.session_id, limit=10)
        for msg in messages:
            memory.short_term.add_message_from_db(msg)
            
        history = memory.get_full_context(user_profile)
        ctx = request.context.model_dump() if request.context else {}
        
        return AgentContext(
            user_id=request.user_id,
            message=request.message,
            task_type=request.task_type,
            subject=ctx.get("subject"),
            education_level=ctx.get("education_level") or (user_profile.education_level if user_profile else None),
            session=session,
            session_id=session.session_id,
            user_profile=user_profile,
            conversation_history=history,
            additional_context={
                "dynamic_memory": dynamic_memory,
                "request": request
            }
        )
    
    async def _make_decision(self, context: AgentContext) -> AgentDecision:
        """决策阶段 (主要判断快慢思考)"""
        data_item = self._build_data_item(context)
        thinking_mode = self.difficulty_decision.decide(data_item)
        
        if context.user_profile and context.user_profile.preferred_thinking_mode != "adaptive":
            thinking_mode = context.user_profile.preferred_thinking_mode
            
        # 默认返回，tool_names 将在 ReAct 循环中动态决定，此处不再硬编码检测
        return AgentDecision(
            thinking_mode=thinking_mode,
            needs_tools=True if thinking_mode in ["slow", "both"] else False,
            tool_names=[]
        )
        
    async def _execute_react_loop(self, context: AgentContext, decision: AgentDecision) -> ExecutionResult:
        """
        核心 ReAct 循环：Thought -> Action -> Action Input -> Observation -> Final Answer
        """
        tool_results = {}
        history_buffer = ""
        system_prompt = self._build_system_prompt(context)
        
        for step in range(self.max_react_steps):
            # 组合当前的完整 Prompt (System + History + Current + ReAct Buffer)
            current_prompt = self._build_turn_prompt(system_prompt, context, history_buffer)
            
            data_item = self._build_data_item(context, custom_prompt=current_prompt)
            # 使用大模型进行一步推导
            response_text = self.inference_engine.infer_slow(data_item)
            history_buffer += f"{response_text}\n"
            
            # 解析工具调用意图
            action_match = re.search(r"Action:\s*(\w+)", response_text)
            action_input_match = re.search(r"Action Input:\s*(```.*?```|.*)", response_text, re.DOTALL)
            
            if action_match and action_input_match:
                tool_name = action_match.group(1).strip()
                action_input = action_input_match.group(1).strip()
                
                # 去除 markdown 代码块
                if action_input.startswith("```"):
                    lines = action_input.split("\n")
                    if len(lines) > 2:
                        action_input = "\n".join(lines[1:-1])
                    else:
                        action_input = action_input.replace("```", "")
                
                # 执行工具
                try:
                    # 根据不同工具的输入格式适配
                    if "python" in tool_name or "sympy" in tool_name:
                        res = await ToolRegistry.execute(tool_name, {"code": action_input})
                    else:
                        # 兼容老工具
                        res = await ToolRegistry.execute(tool_name, {"expression": action_input, "keyword": action_input})
                        
                    observation = res.data if res.success else f"Error: {res.error}"
                except Exception as e:
                    observation = f"Tool Error: {str(e)}"
                    res = None
                    
                if res:
                    tool_results[f"{tool_name}_{step}"] = res
                
                # 将观察结果喂回给大模型
                history_buffer += f"Observation:\n{observation}\nThought: "
            else:
                # 未匹配到 Action，说明模型认为推导结束，输出了 Final Answer
                break
                
        # 提取最终答案
        final_answer_match = re.search(r"Final Answer:\s*(.*)", history_buffer, re.DOTALL)
        final_response = final_answer_match.group(1).strip() if final_answer_match else history_buffer
        
        return ExecutionResult(
            response=final_response,
            thinking_mode=decision.thinking_mode,
            tool_results=tool_results
        )

    async def _execute_fast(self, context: AgentContext, decision: AgentDecision) -> ExecutionResult:
        """快思考执行"""
        system_prompt = self._build_system_prompt(context)
        prompt = self._build_turn_prompt(system_prompt, context, "")
        data_item = self._build_data_item(context, custom_prompt=prompt)
        response = self.inference_engine.infer_fast(data_item)
        
        return ExecutionResult(
            response=response,
            thinking_mode=decision.thinking_mode,
            tool_results={}
        )

    async def _post_process(self, context: AgentContext, result: ExecutionResult, start_time: float, db_session) -> ChatResponse:
        """后处理并持久化"""
        latency_ms = int((time.time() - start_time) * 1000)
        message_id = str(uuid.uuid4())
        
        # 保存对话
        await self.session_manager.add_message(db_session, context.session.session_id, role="user", content=context.message)
        
        tool_call_records = []
        for k, v in result.tool_results.items():
            if v:
                tool_call_records.append(f"{k}: success={v.success}")
                
        await self.session_manager.add_message(
            db_session, context.session.session_id, role="assistant",
            content=result.response, thinking_mode=result.thinking_mode,
            latency_ms=latency_ms, tool_calls=tool_call_records
        )
        
        # 更新用户统计
        await self.user_profile_service.increment_stats(db_session, context.user_id)
        if context.session.message_count == 0:
            await self.session_manager.update_title(db_session, context.session.session_id, context.message[:50])
            
        return ChatResponse(
            session_id=context.session.session_id,
            message_id=message_id,
            response=result.response,
            thinking_mode=result.thinking_mode,
            metadata=ChatMetadata(
                tokens_used=len(result.response),
                latency_ms=latency_ms,
                tool_calls=tool_call_records
            )
        )
        
    def _build_system_prompt(self, context: AgentContext) -> str:
        """根据上下文构建系统 Prompt"""
        user_context = ""
        if context.user_profile:
            user_context = f"学制级别: {context.user_profile.education_level or '未知'}"
            
        dynamic_memory = context.additional_context.get("dynamic_memory", "")
        return build_system_prompt(
            user_context=user_context,
            dynamic_memory=dynamic_memory,
            task_type=context.task_type or "question_answering",
            subject=context.subject or "通用",
            history=context.conversation_history
        )
        
    def _build_turn_prompt(self, system_prompt: str, context: AgentContext, react_buffer: str) -> str:
        """构建单次喂给模型的 Prompt"""
        parts = [system_prompt]
        parts.append(f"\n用户问题: {context.message}")
        if react_buffer:
            parts.append(f"\n推导过程:\n{react_buffer}")
        else:
            parts.append("\n推导过程:\nThought: ")
        return "\n".join(parts)

    def _build_data_item(self, context: AgentContext, custom_prompt: str = None) -> DataItem:
        return DataItem(
            task_type=context.task_type or "question_answering",
            prompt=custom_prompt if custom_prompt else context.message,
            question=context.message,
            subject=context.subject or "",
            education_level=context.education_level or (context.user_profile.education_level if context.user_profile else ""),
            question_type=context.additional_context.get("question_type", ""),
            lang="zh" if any('\u4e00' <= c <= '\u9fff' for c in context.message) else "en"
        )

# 单例
_agent_core: AgentCore | None = None

def get_agent_core() -> AgentCore:
    global _agent_core
    if _agent_core is None:
        _agent_core = AgentCore()
    return _agent_core
