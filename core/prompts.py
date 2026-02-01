"""
系统提示词模板
"""

# 基础系统提示词
SYSTEM_PROMPT_BASE = """你是盘古教育助手，一个专业的教育辅导AI，基于华为盘古Embedded 7B模型。

## 核心原则
1. 耐心细致地回答学生问题
2. 根据学生水平调整解答难度和详细程度
3. 鼓励学生思考，引导而非直接给答案
4. 使用清晰的步骤和示例
5. 对薄弱环节提供更详细的解释

## 回答格式
- 结构清晰，分步骤说明
- 重点内容适当强调
- 必要时给出示例
"""

# 带用户上下文的提示词模板
SYSTEM_PROMPT_WITH_USER = """你是盘古教育助手，一个专业的教育辅导AI。

{user_context}

## 当前任务
- 任务类型：{task_type}
- 学科：{subject}

## 指导原则
1. 根据用户水平调整解答难度
2. 对薄弱环节提供更详细的解释
3. 鼓励用户思考，引导而非直接给答案
4. 使用清晰的步骤和示例

## 对话历史
{history}
"""

# 快思考提示词模板
FAST_THINKING_PROMPT_ZH = """请直接回答以下问题：

{question}

答案："""

FAST_THINKING_PROMPT_EN = """Answer the following question directly:

{question}

Answer:"""

# 慢思考提示词模板
SLOW_THINKING_PROMPT_ZH = """请逐步分析并回答以下问题：

{question}

让我们一步一步思考：
"""

SLOW_THINKING_PROMPT_EN = """Let's think step by step to answer:

{question}

Step-by-step thinking:
"""

# 基于慢思考结果的快思考提示词
FAST_FROM_SLOW_PROMPT_ZH = """基于以下详细分析，请给出简洁的最终答案：

问题：
{question}

详细分析：
{slow_response}

请根据上述分析，直接给出最终答案（简洁明了）：
"""

FAST_FROM_SLOW_PROMPT_EN = """Based on the detailed analysis below, provide a concise final answer:

Question:
{question}

Detailed Analysis:
{slow_response}

Final Answer (concise):
"""

# 任务类型特定提示词
TASK_PROMPTS_ZH = {
    "question_answering": {
        "fast": "请直接回答以下问题：\n\n{question}\n\n答案：",
        "slow": "请逐步分析并回答以下问题：\n\n{question}\n\n让我们一步一步思考：\n"
    },
    "automatic_grading": {
        "fast": "请对以下学生答案进行评分：\n\n{question}\n\n评分结果：",
        "slow": "请详细分析并评分以下学生答案：\n\n{question}\n\n评分分析：\n1. 首先分析答案的优点\n2. 然后指出不足\n3. 最后给出评分和建议\n\n"
    },
    "error_correction": {
        "fast": "请指出以下答案的错误并给出正确答案：\n\n{question}\n\n纠错：",
        "slow": "请仔细分析以下答案的错误：\n\n{question}\n\n纠错分析：\n1. 识别错误之处\n2. 解释为什么错误\n3. 给出正确答案\n\n"
    },
    "idea_prompting": {
        "fast": "请为以下问题提供解题思路：\n\n{question}\n\n思路：",
        "slow": "请为以下问题提供详细的解题思路：\n\n{question}\n\n解题思路：\n1. 问题分析\n2. 解题步骤\n3. 关键点提示\n\n"
    },
    "personalized_content": {
        "fast": "请根据要求设计学习内容：\n\n{question}\n\n学习内容：",
        "slow": "请根据学生画像设计个性化学习内容：\n\n{question}\n\n设计思路：\n1. 分析学生特点\n2. 确定学习目标\n3. 设计学习内容\n\n"
    },
    "personalized_learning": {
        "fast": "请为学生规划学习路径：\n\n{question}\n\n学习路径：",
        "slow": "请为学生规划个性化学习路径：\n\n{question}\n\n规划思路：\n1. 评估当前水平\n2. 设定学习目标\n3. 安排学习路径\n\n"
    },
    "question_generation": {
        "fast": "请根据知识点生成题目：\n\n{question}\n\n题目：",
        "slow": "请根据知识点生成高质量题目：\n\n{question}\n\n生成思路：\n1. 分析知识点\n2. 设计题目类型\n3. 编写题目和答案\n\n"
    },
    "teaching_material": {
        "fast": "请设计教学素材：\n\n{question}\n\n教学素材：",
        "slow": "请设计教学素材：\n\n{question}\n\n设计思路：\n1. 教学目标\n2. 重点难点\n3. 活动设计\n\n"
    }
}

# 默认提示词
DEFAULT_PROMPT_ZH = {
    "fast": "请完成以下任务：\n\n{question}\n\n回答：",
    "slow": "请详细分析并完成以下任务：\n\n{question}\n\n分析过程：\n"
}


def get_task_prompt(task_type: str, mode: str, lang: str = "zh") -> str:
    """获取任务类型对应的提示词模板"""
    if lang == "zh":
        prompts = TASK_PROMPTS_ZH.get(task_type, DEFAULT_PROMPT_ZH)
        return prompts.get(mode, DEFAULT_PROMPT_ZH[mode])
    else:
        # 英文版本简化处理
        if mode == "fast":
            return "Complete the following task:\n\n{question}\n\nResponse:"
        else:
            return "Analyze and complete the task in detail:\n\n{question}\n\nAnalysis:\n"


def build_system_prompt(
    user_context: str = "",
    task_type: str = "",
    subject: str = "",
    history: str = ""
) -> str:
    """构建系统提示词"""
    if not user_context and not history:
        return SYSTEM_PROMPT_BASE
    
    return SYSTEM_PROMPT_WITH_USER.format(
        user_context=user_context or "无用户信息",
        task_type=task_type or "通用问答",
        subject=subject or "通用",
        history=history or "无历史对话"
    )
