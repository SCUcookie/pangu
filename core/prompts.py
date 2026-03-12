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

# 自我评估提示词 (创新点二：元认知反馈)
SELF_EVAL_PROMPT_ZH = """请你作为一名教育评估专家，对以下模型给出的初始回答进行批判性自我评估。

【原问题】：
{question}

【初始回答】：
{fast_response}

【评估标准】：
1. **准确性**：回答是否事实正确？是否有数学或逻辑错误？
2. **完整性**：是否完整回答了问题的所有部分？
3. **教育引导**：是否遵循了苏格拉底式的教学引导（而不是直接给答案）？

请在以下三个选项中选择一个最符合的标签，并给出简短理由：
- [[Confident]]：回答完全正确、专业且符合教育原则。
- [[Uncertain]]：回答大致正确，但在细节、严谨性或引导方式上存在不确定性。
- [[Incorrect]]：回答存在明显事实错误、逻辑漏洞或严重违反教学原则。

评估结论（仅输出标签和理由）：
"""

# GPT-5.4 专家评估提示词 (Model-as-a-Judge)
GPT5_JUDGE_PROMPT_ZH = """你是一位顶尖的教育专家和语言模型评估者。请对以下模型生成的回答进行多维度评分。

【评估背景】：
- 场景类型：{task_type}
- 题目内容：{question}
- 标准答案（仅供参考）：{ground_truth}

【待评估回答】：
{prediction}

【评分维度 (1-10分)】：
1. **场景自适应 (Scenario Adaptability)**：
   - 指令遵循与任务完成 (IFTC)
   - 角色与语气一致性 (RTC)
   - 内容相关性与范围控制 (CRSC)
2. **事实与逻辑准确性 (Factual & Reasoning Accuracy)**：
   - 基础事实准确性 (BFA)
   - 领域知识准确性 (DKA)
   - 推理过程严密性 (RPR)
3. **教育应用价值 (Pedagogical Application)**：
   - 清晰、简洁与启发性 (CSI)
   - 动力、引导与正向反馈 (MGP)
   - 高阶思维与技能培养 (HOTS)

【评分要求】：
- 请基于标准答案和教育学原则，客观、严苛地给出各项分数。
- 必须以 JSON 格式输出，包含各子项分数和总分（Average）。

【输出格式示例】：
{{
  "IFTC": 9, "RTC": 9, "CRSC": 8,
  "BFA": 10, "DKA": 10, "RPR": 9,
  "CSI": 8, "MGP": 7, "HOTS": 8,
  "Average": 8.7,
  "Reason": "理由简述..."
}}
"""

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
