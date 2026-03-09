"""
Agent核心控制器
整合记忆、工具、用户画像、推理引擎，协调完成用户请求
"""
import uuid
import time
from typing import Any
from datetime import datetime

from .context import AgentContext, AgentDecision, ExecutionResult
from .prompts import build_system_prompt
from .memory.manager import MemoryManager
from .tools.registry import ToolRegistry
from .tools.builtin import register_builtin_tools

import sys
sys.path.insert(0, '/opt/pangu/ldh/agentv2')

from difficulty_decision import DifficultyDecision
from inference_engine import InferenceEngine
from data_loader import DataItem
from services.user_profile import UserProfileService
from services.session_manager import SessionManager
from api.schemas.chat import ChatRequest, ChatResponse, ChatMetadata
from db.models import LearningRecord


class AgentCore:
    """Agent核心控制器"""
    
    def __init__(self):
        self.inference_engine = InferenceEngine()
        self.difficulty_decision = DifficultyDecision()
        self.user_profile_service = UserProfileService()
        self.session_manager = SessionManager()
        
        # 注册内置工具
        register_builtin_tools()
    
    async def process(self, request: ChatRequest, db_session) -> ChatResponse:
        """处理用户请求的主入口"""
        start_time = time.time()
        
        # 1. 初始化上下文
        context = await self._init_context(request, db_session)
        
        # 2. 决策
        decision = await self._make_decision(context)
        
        # 3. 执行
        result = await self._execute(context, decision)
        
        # 4. 后处理
        response = await self._post_process(context, result, start_time, db_session)
        
        return response
    
    async def _init_context(self, request: ChatRequest, db_session) -> AgentContext:
        """初始化上下文"""
        # 获取或创建会话
        if request.session_id:
            session = await self.session_manager.get_session(db_session, request.session_id)
            if not session:
                session = await self.session_manager.create_session(
                    db_session, request.user_id,
                    task_type=request.task_type,
                    subject=request.context.subject if request.context else None
                )
        else:
            session = await self.session_manager.create_session(
                db_session, request.user_id,
                task_type=request.task_type,
                subject=request.context.subject if request.context else None
            )
        
        # 获取用户画像
        user_profile = await self.user_profile_service.get_profile(db_session, request.user_id)
        if not user_profile:
            user_profile = await self.user_profile_service.create_profile(db_session, request.user_id)
        
        # 构建记忆管理器
        memory = MemoryManager(request.user_id, session.session_id)
        
        # 加载对话历史
        messages = await self.session_manager.get_messages(db_session, session.session_id, limit=20)
        for msg in messages:
            memory.short_term.add_message_from_db(msg)
        
        # 获取完整上下文
        history = memory.get_full_context(user_profile)
        
        # 提取context中的信息
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
            additional_context={"memory": memory, "request": request}
        )
    
    async def _make_decision(self, context: AgentContext) -> AgentDecision:
        """决策阶段"""
        # 构造DataItem用于难度决策
        data_item = self._build_data_item(context)
        
        # 基础难度决策
        thinking_mode = self.difficulty_decision.decide(data_item)
        
        # 根据用户画像调整
        if context.user_profile:
            preferred = context.user_profile.preferred_thinking_mode
            if preferred and preferred != "adaptive":
                thinking_mode = preferred
        
        # 判断是否需要工具
        needs_tools, tool_names = self._detect_tool_needs(context.message)
        
        return AgentDecision(
            thinking_mode=thinking_mode,
            needs_tools=needs_tools,
            tool_names=tool_names
        )
    
    async def _execute(self, context: AgentContext, decision: AgentDecision) -> ExecutionResult:
        """执行阶段"""
        tool_results = {}
        
        # 如果需要工具，先执行工具
        if decision.needs_tools:
            for tool_name in decision.tool_names:
                params = self._extract_tool_params(context, tool_name)
                result = await ToolRegistry.execute(tool_name, params)
                tool_results[tool_name] = result
        
        # 构建最终prompt
        prompt = self._build_prompt(context, tool_results)
        
        # 构造DataItem用于推理
        data_item = self._build_data_item(context)
        
        # 执行推理
        if decision.thinking_mode == "fast":
            response = self.inference_engine.infer_fast(data_item)
        elif decision.thinking_mode == "slow":
            response = self.inference_engine.infer_slow(data_item)
        else:  # both
            result = self.inference_engine.infer_slow_then_fast(data_item)
            response = f"【详细分析】\n{result['slow_thinking']}\n\n【简洁答案】\n{result['fast_answer']}"
        
        return ExecutionResult(
            response=response,
            thinking_mode=decision.thinking_mode,
            tool_results=tool_results
        )
    
    async def _post_process(
        self, 
        context: AgentContext, 
        result: ExecutionResult, 
        start_time: float,
        db_session
    ) -> ChatResponse:
        """后处理阶段"""
        latency_ms = int((time.time() - start_time) * 1000)
        message_id = str(uuid.uuid4())
        
        # 保存用户消息
        await self.session_manager.add_message(
            db_session,
            context.session.session_id,
            role="user",
            content=context.message
        )
        
        # 保存助手消息
        await self.session_manager.add_message(
            db_session,
            context.session.session_id,
            role="assistant",
            content=result.response,
            thinking_mode=result.thinking_mode,
            latency_ms=latency_ms,
            tool_calls=list(result.tool_results.keys())
        )
        
        # 更新用户统计
        await self.user_profile_service.increment_stats(
            db_session, 
            context.user_id
        )
        
        # 如果是首条消息，生成会话标题
        if context.session.message_count == 0:
            title = context.message[:50]
            await self.session_manager.update_title(
                db_session, 
                context.session.session_id, 
                title
            )
        
        # 构建响应
        return ChatResponse(
            session_id=context.session.session_id,
            message_id=message_id,
            response=result.response,
            thinking_mode=result.thinking_mode,
            metadata=ChatMetadata(
                tokens_used=len(result.response),  # 简化估算
                latency_ms=latency_ms,
                tool_calls=list(result.tool_results.keys())
            )
        )
    
    def _build_data_item(self, context: AgentContext) -> DataItem:
        """构建DataItem用于现有模块"""
        return DataItem(
            task_type=context.task_type or "question_answering",
            prompt=context.message,
            question=context.message,
            subject=context.subject or "",
            education_level=context.education_level or (
                context.user_profile.education_level if context.user_profile else ""),
            question_type=context.additional_context.get("question_type", ""),
            lang="zh" if any('\u4e00' <= c <= '\u9fff' for c in context.message) else "en"
        )
    
    def _detect_tool_needs(self, message: str) -> tuple[bool, list[str]]:
        """检测是否需要调用工具"""
        tools_needed = []
        message_lower = message.lower()
        
        # 计算相关关键词
        calc_keywords = ["计算", "算", "等于", "求值", "calculate", "compute", "+", "-", "*", "/", "="]
        if any(kw in message_lower for kw in calc_keywords):
            # 检查是否包含数学表达式
            import re
            if re.search(r'\d+\s*[\+\-\*\/\%\^]\s*\d+', message):
                tools_needed.append("calculator")
        
        # 公式查询关键词
        formula_keywords = ["公式", "formula", "定理", "theorem"]
        if any(kw in message_lower for kw in formula_keywords):
            tools_needed.append("formula_lookup")
        
        # 知识查询关键词
        knowledge_keywords = ["什么是", "解释", "定义", "概念", "what is", "explain", "definition"]
        if any(kw in message_lower for kw in knowledge_keywords):
            tools_needed.append("knowledge")
        
        return len(tools_needed) > 0, tools_needed
    
    def _extract_tool_params(self, context: AgentContext, tool_name: str) -> dict:
        """从上下文中提取工具参数"""
        message = context.message
        
        if tool_name == "calculator":
            # 尝试提取数学表达式
            import re
            match = re.search(r'[\d\s\+\-\*\/\(\)\.\^]+', message)
            expr = match.group(0).strip() if match else message
            return {"expression": expr}
        
        elif tool_name == "formula_lookup":
            return {
                "subject": context.subject or "数学",
                "keyword": message
            }
        
        elif tool_name == "knowledge":
            return {
                "subject": context.subject or "数学",
                "topic": message
            }
        
        return {}
    
    def _build_prompt(self, context: AgentContext, tool_results: dict) -> str:
        """构建最终prompt"""
        parts = []
        
        # 构建用户上下文
        user_context = ""
        if context.user_profile:
            user_context = f"学制级别: {context.user_profile.education_level or '未知'}"
        
        # 系统提示
        system_prompt = build_system_prompt(
            user_context=user_context,
            task_type=context.task_type or "question_answering",
            subject=context.subject or "通用",
            history=""
        )
        parts.append(system_prompt)
        
        # 工具结果
        if tool_results:
            parts.append("\n【工具调用结果】")
            for tool_name, result in tool_results.items():
                if result.success:
                    parts.append(f"- {tool_name}: {result.data}")
                else:
                    parts.append(f"- {tool_name}: 调用失败 - {result.error}")
        
        # 对话历史
        if context.conversation_history:
            parts.append(f"\n{context.conversation_history}")
        
        # 当前问题
        parts.append(f"\n用户: {context.message}")
        parts.append("\n助手: ")
        
        return "\n".join(parts)


# 单例
_agent_core: AgentCore | None = None


def get_agent_core() -> AgentCore:
    """获取Agent核心实例"""
    global _agent_core
    if _agent_core is None:
        _agent_core = AgentCore()
    return _agent_core
