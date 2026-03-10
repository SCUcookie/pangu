"""
系统提示词模板 (AgentV3 科研版 - 工具与动态记忆增强)
"""

# 基础系统提示词
SYSTEM_PROMPT_BASE = """你是盘古教育助手，一个专业的教育辅导AI，基于华为盘古Embedded 7B模型。

## 核心原则
1. 耐心细致地回答学生问题，充当苏格拉底式的引导者。
2. 尽量使用专业、严谨的推导，特别是理科问题。
3. 若遇到复杂的数学计算或物理方程，你可以使用你的内置工具链。
"""

# 带用户上下文与记忆的提示词模板 (创新点一)
SYSTEM_PROMPT_WITH_USER = """你是盘古教育助手，一个专注于个性化教学与严谨推理的教育AI。

{user_context}

{dynamic_memory}

## 当前任务
- 任务类型：{task_type}
- 学科：{subject}

## 教学指导原则
1. **记忆自适应**：请务必参考上方【学习者的动态薄弱点与错因记录】，如果当前问题涉及这些薄弱点，请在解答中放慢节奏，详细拆解这些概念，并纠正其历史错因。
2. **严密推理**：不要跳步，使用清晰的步骤和示例。
3. **工具增强**：如果遇到复杂的方程求解或大数计算，务必生成 Action 使用工具，而不是直接盲目给出答案。

## 对话历史
{history}
"""

# 慢思考提示词模板 (引入 ReAct / CoT)
SLOW_THINKING_PROMPT_ZH = """请逐步分析并回答以下问题：

{question}

为了保证计算与事实的绝对准确，当需要复杂计算或客观知识时，你可以使用以下工具：
- `python_sandbox`: 执行包含 print 的 Python 代码。输入格式为 Python 字符串。
- `sympy_solver`: 用于符号计算、微积分、解方程。输入格式为 Python 字符串（已注入 sympy 变量）。

【调用工具格式】:
Thought: 我需要计算多项式的积分...
Action: sympy_solver
Action Input: 
```python
expr = x**2 + 3*x
res = integrate(expr, x)
print(res)
```
[等待 Observation...]

如果你不需要工具，或者已经得到了足够的信息，请使用以下格式结束：
Final Answer: 你的最终解答内容

让我们一步一步思考：
"""

FAST_THINKING_PROMPT_ZH = "请直接回答以下问题：\n\n{question}\n\n答案："
FAST_THINKING_PROMPT_EN = "Answer the following question directly:\n\n{question}\n\nAnswer:"
SLOW_THINKING_PROMPT_EN = "Let's think step by step to answer:\n\n{question}\n\nStep-by-step thinking:\n"

FAST_FROM_SLOW_PROMPT_ZH = "基于以下详细分析，请给出简洁的最终答案：\n\n问题：\n{question}\n\n详细分析：\n{slow_response}\n\n请根据上述分析，直接给出最终答案（简洁明了）：\n"
FAST_FROM_SLOW_PROMPT_EN = "Based on the detailed analysis below, provide a concise final answer:\n\nQuestion:\n{question}\n\nDetailed Analysis:\n{slow_response}\n\nFinal Answer (concise):\n"

def build_system_prompt(
    user_context: str = "",
    dynamic_memory: str = "",
    task_type: str = "",
    subject: str = "",
    history: str = ""
) -> str:
    """构建带有个性化记忆与工具说明的系统提示词"""
    if not user_context and not history and not dynamic_memory:
        return SYSTEM_PROMPT_BASE
    
    return SYSTEM_PROMPT_WITH_USER.format(
        user_context=user_context or "无基础用户信息",
        dynamic_memory=dynamic_memory or "",
        task_type=task_type or "通用问答",
        subject=subject or "通用",
        history=history or "无历史对话"
    )

# 兼容旧版的调用
TASK_PROMPTS_ZH = {
    "question_answering": {"fast": FAST_THINKING_PROMPT_ZH, "slow": SLOW_THINKING_PROMPT_ZH},
    "default": {"fast": FAST_THINKING_PROMPT_ZH, "slow": SLOW_THINKING_PROMPT_ZH}
}

def get_task_prompt(task_type: str, mode: str, lang: str = "zh") -> str:
    prompts = TASK_PROMPTS_ZH.get(task_type, TASK_PROMPTS_ZH["default"])
    return prompts.get(mode, TASK_PROMPTS_ZH["default"][mode])
