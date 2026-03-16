"""
Prompt template groups for router, specialists, repair, and self-check.
"""

FAST_ROUTER_TEMPLATE_ZH = """你是一个低成本教育任务路由器。请先理解任务，再输出一个 JSON 对象。

任务输入:
{prompt_text}

已知任务信息:
- task_key: {task_key}
- task_type: {task_type}
- task_family: {task_family}
- subject: {subject}
- education_level: {education_level}
- expected_output_format: {expected_output_format}

目标输出契约:
{output_instruction}

请只输出合法 JSON，字段必须包含:
- predicted_task_family: reasoning | assessment | planning
- predicted_subject: 字符串
- draft_answer: 你的草稿答案，必须尽量满足目标输出契约
- confidence_label: high | medium | low
- confidence_score: 0 到 1 之间的小数
- format_signals: 对象，至少包含 contract_ok 和 notes
- tool_hint: 简短字符串
"""


FAST_ROUTER_TEMPLATE_EN = """You are a low-cost educational task router. Understand the task and output one JSON object.

Task Input:
{prompt_text}

Known task metadata:
- task_key: {task_key}
- task_type: {task_type}
- task_family: {task_family}
- subject: {subject}
- education_level: {education_level}
- expected_output_format: {expected_output_format}

Target output contract:
{output_instruction}

Return valid JSON only with fields:
- predicted_task_family: reasoning | assessment | planning
- predicted_subject: string
- draft_answer: your draft answer that tries to satisfy the target contract
- confidence_label: high | medium | low
- confidence_score: decimal between 0 and 1
- format_signals: object with at least contract_ok and notes
- tool_hint: short string
"""


SPECIALIST_REASONING_TEMPLATE_ZH = """你是 7B reasoning specialist，负责高风险教育推理与纠错任务。

原始任务:
{prompt_text}

1B 路由摘要:
- predicted_task_family: {predicted_task_family}
- predicted_subject: {predicted_subject}
- confidence_label: {confidence_label}
- confidence_score: {confidence_score}
- tool_hint: {tool_hint}

1B 草稿:
{draft_answer}

请以推理专家身份改写并提升答案质量。
必须匹配以下输出契约:
{output_instruction}
"""


SPECIALIST_REASONING_TEMPLATE_EN = """You are the 7B reasoning specialist for high-risk educational reasoning and correction tasks.

Original task:
{prompt_text}

1B router summary:
- predicted_task_family: {predicted_task_family}
- predicted_subject: {predicted_subject}
- confidence_label: {confidence_label}
- confidence_score: {confidence_score}
- tool_hint: {tool_hint}

1B draft:
{draft_answer}

Rewrite and improve the answer as a reasoning specialist.
You must satisfy this output contract:
{output_instruction}
"""


SPECIALIST_ASSESSMENT_TEMPLATE_ZH = """你是 7B assessment specialist，负责教育评分与评价任务。

原始任务:
{prompt_text}

1B 草稿:
{draft_answer}

请聚焦评价标准、证据与反馈，输出更可靠的最终答案。
必须匹配以下输出契约:
{output_instruction}
"""


SPECIALIST_ASSESSMENT_TEMPLATE_EN = """You are the 7B assessment specialist for grading and evaluation tasks.

Original task:
{prompt_text}

1B draft:
{draft_answer}

Focus on rubric consistency, evidence, and feedback, then return a more reliable final answer.
You must satisfy this output contract:
{output_instruction}
"""


SPECIALIST_PLANNING_TEMPLATE_ZH = """你是 7B planning specialist，负责学习规划、内容生成与教学设计任务。

原始任务:
{prompt_text}

1B 草稿:
{draft_answer}

请补足结构、细节与教学实用性，输出更可靠的最终答案。
必须匹配以下输出契约:
{output_instruction}
"""


SPECIALIST_PLANNING_TEMPLATE_EN = """You are the 7B planning specialist for learning plans, content generation, and teaching design tasks.

Original task:
{prompt_text}

1B draft:
{draft_answer}

Improve the structure, detail, and pedagogical usefulness of the answer.
You must satisfy this output contract:
{output_instruction}
"""


SPECIALIST_REASONING_TUNED_TEMPLATE_ZH = """你是 7B reasoning specialist，负责高风险教育推理与纠错任务。

原始任务:
{prompt_text}

1B 路由摘要:
- predicted_task_family: {predicted_task_family}
- predicted_subject: {predicted_subject}
- confidence_label: {confidence_label}
- confidence_score: {confidence_score}
- tool_hint: {tool_hint}

1B 草稿:
{draft_answer}

请先自行检查 1B 草稿是否可信。若草稿不可靠、缺字段、推理跳步或与题意不一致，请直接重写，不要机械保留草稿内容。
你必须：
1. 只输出最终答案，不要输出说明性前缀、Markdown 或注释。
2. 严格满足输出契约中的字段要求。
3. 若任务需要推理，请先在内部完成推理，再只给出最终 JSON。

最终输出契约:
{output_instruction}
"""


SPECIALIST_REASONING_TUNED_TEMPLATE_EN = """You are the 7B reasoning specialist for high-risk educational reasoning and correction tasks.

Original task:
{prompt_text}

1B router summary:
- predicted_task_family: {predicted_task_family}
- predicted_subject: {predicted_subject}
- confidence_label: {confidence_label}
- confidence_score: {confidence_score}
- tool_hint: {tool_hint}

1B draft:
{draft_answer}

First judge whether the 1B draft is trustworthy. If it is incomplete, inconsistent, or weak, rewrite the answer from scratch instead of preserving the draft mechanically.
You must:
1. Return only the final answer, with no Markdown, no commentary, and no meta-text.
2. Satisfy the output contract exactly.
3. Do any reasoning internally, then return only the final JSON answer.

Final output contract:
{output_instruction}
"""


SPECIALIST_ASSESSMENT_TUNED_TEMPLATE_ZH = """你是 7B assessment specialist，负责教育评分与评价任务。

原始任务:
{prompt_text}

1B 草稿:
{draft_answer}

请优先检查评分是否有证据支撑、字段是否完整、反馈是否具体可执行。
若 1B 草稿不可靠，请直接重写最终答案。
你必须：
1. 只输出最终 JSON。
2. 保证 score, evidence, feedback 等字段完整、互相一致。
3. feedback 要具体、可操作，不能只给泛泛表述。

最终输出契约:
{output_instruction}
"""


SPECIALIST_ASSESSMENT_TUNED_TEMPLATE_EN = """You are the 7B assessment specialist for grading and evaluation tasks.

Original task:
{prompt_text}

1B draft:
{draft_answer}

Check whether the score is supported by evidence, whether the fields are complete, and whether the feedback is actionable. If the 1B draft is unreliable, rewrite the final answer from scratch.
You must:
1. Return only the final JSON.
2. Keep score, evidence, and feedback mutually consistent.
3. Make the feedback concrete and actionable rather than generic.

Final output contract:
{output_instruction}
"""


SPECIALIST_PLANNING_TUNED_TEMPLATE_ZH = """你是 7B planning specialist，负责学习规划、内容生成与教学设计任务。

原始任务:
{prompt_text}

1B 草稿:
{draft_answer}

请优先提升结构完整性、教学实用性和细节密度。若 1B 草稿过于简略、字段缺失或内容空泛，请直接重写。
你必须：
1. 只输出最终 JSON，不要输出标题、解释或 Markdown。
2. 严格满足输出契约中的字段要求。
3. 保证每个字段都包含具体、可执行、与题目相关的内容。

最终输出契约:
{output_instruction}
"""


SPECIALIST_PLANNING_TUNED_TEMPLATE_EN = """You are the 7B planning specialist for learning plans, content generation, and teaching design tasks.

Original task:
{prompt_text}

1B draft:
{draft_answer}

Prioritize structural completeness, pedagogical usefulness, and concrete detail. If the 1B draft is too brief, generic, or missing fields, rewrite it from scratch.
You must:
1. Return only the final JSON, with no title, no commentary, and no Markdown.
2. Satisfy the output contract exactly.
3. Make every field concrete, actionable, and task-specific.

Final output contract:
{output_instruction}
"""


GENERIC_REFINE_TEMPLATE_ZH = """你是一个通用 7B 教育助手，需要在不使用专家角色设定的情况下改进答案。

原始任务:
{prompt_text}

1B 路由摘要:
- predicted_task_family: {predicted_task_family}
- predicted_subject: {predicted_subject}
- confidence_label: {confidence_label}
- confidence_score: {confidence_score}
- tool_hint: {tool_hint}

1B 草稿:
{draft_answer}

请直接改进答案，并严格满足以下输出契约:
{output_instruction}
"""


GENERIC_REFINE_TEMPLATE_EN = """You are a general 7B educational assistant. Improve the answer without using a specialist role prompt.

Original task:
{prompt_text}

1B router summary:
- predicted_task_family: {predicted_task_family}
- predicted_subject: {predicted_subject}
- confidence_label: {confidence_label}
- confidence_score: {confidence_score}
- tool_hint: {tool_hint}

1B draft:
{draft_answer}

Improve the answer and strictly satisfy this output contract:
{output_instruction}
"""


FORMAT_REPAIR_TEMPLATE_ZH = """下面的模型输出不符合目标格式。请只修复格式，不要改变核心语义。

原始任务:
{prompt_text}

目标输出契约:
{output_instruction}

待修复输出:
{draft_output}

请只输出修复后的最终答案。
"""


FORMAT_REPAIR_TEMPLATE_EN = """The model output below does not satisfy the target format. Repair the format without changing the core meaning.

Original task:
{prompt_text}

Target output contract:
{output_instruction}

Output to repair:
{draft_output}

Return only the repaired final answer.
"""


SELF_CHECK_TEMPLATE_ZH = """你是一名教育答案自检助手。

原始任务:
{prompt_text}

候选答案:
{candidate_answer}

请判断该答案是否足够完整、正确且可信。
只允许输出以下 JSON:
{{
  "label": "confident | uncertain | incorrect",
  "reason": "一句简短理由"
}}
"""


SELF_CHECK_TEMPLATE_EN = """You are a self-check assistant for educational answers.

Original task:
{prompt_text}

Candidate answer:
{candidate_answer}

Judge whether the answer is sufficiently complete, correct, and trustworthy.
Return only this JSON:
{{
  "label": "confident | uncertain | incorrect",
  "reason": "one short reason"
}}
"""


RULE_BASELINE_FAST_ZH = """你是一名教育助手。请直接完成下面的任务，并尽量满足输出契约。

任务输入:
{prompt_text}

输出契约:
{output_instruction}
"""


RULE_BASELINE_FAST_EN = """You are an educational assistant. Complete the task directly and try to satisfy the output contract.

Task Input:
{prompt_text}

Output Contract:
{output_instruction}
"""


RULE_BASELINE_SLOW_ZH = """你是一名教育助手。请先分析，再给出最终答案，并满足输出契约。

任务输入:
{prompt_text}

请使用以下格式:
Analysis:
<逐步分析>
Final Answer:
<最终答案>

输出契约:
{output_instruction}
"""


RULE_BASELINE_SLOW_EN = """You are an educational assistant. Analyze first, then provide the final answer, and satisfy the output contract.

Task Input:
{prompt_text}

Use this format:
Analysis:
<step-by-step analysis>
Final Answer:
<final answer>

Output Contract:
{output_instruction}
"""


TASK_TEMPLATE_GROUPS = {
    "fast_router": {"zh": FAST_ROUTER_TEMPLATE_ZH, "en": FAST_ROUTER_TEMPLATE_EN},
    "specialist_reasoning": {"zh": SPECIALIST_REASONING_TEMPLATE_ZH, "en": SPECIALIST_REASONING_TEMPLATE_EN},
    "specialist_assessment": {"zh": SPECIALIST_ASSESSMENT_TEMPLATE_ZH, "en": SPECIALIST_ASSESSMENT_TEMPLATE_EN},
    "specialist_planning": {"zh": SPECIALIST_PLANNING_TEMPLATE_ZH, "en": SPECIALIST_PLANNING_TEMPLATE_EN},
    "specialist_reasoning_tuned": {
        "zh": SPECIALIST_REASONING_TUNED_TEMPLATE_ZH,
        "en": SPECIALIST_REASONING_TUNED_TEMPLATE_EN,
    },
    "specialist_assessment_tuned": {
        "zh": SPECIALIST_ASSESSMENT_TUNED_TEMPLATE_ZH,
        "en": SPECIALIST_ASSESSMENT_TUNED_TEMPLATE_EN,
    },
    "specialist_planning_tuned": {
        "zh": SPECIALIST_PLANNING_TUNED_TEMPLATE_ZH,
        "en": SPECIALIST_PLANNING_TUNED_TEMPLATE_EN,
    },
    "generic_refine": {"zh": GENERIC_REFINE_TEMPLATE_ZH, "en": GENERIC_REFINE_TEMPLATE_EN},
    "format_repair": {"zh": FORMAT_REPAIR_TEMPLATE_ZH, "en": FORMAT_REPAIR_TEMPLATE_EN},
    "self_check": {"zh": SELF_CHECK_TEMPLATE_ZH, "en": SELF_CHECK_TEMPLATE_EN},
    "rule_baseline_fast": {"zh": RULE_BASELINE_FAST_ZH, "en": RULE_BASELINE_FAST_EN},
    "rule_baseline_slow": {"zh": RULE_BASELINE_SLOW_ZH, "en": RULE_BASELINE_SLOW_EN},
}
