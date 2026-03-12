"""
推理引擎 - AgentV2
使用vLLM进行快思考和慢思考推理
"""
import requests
import json
from typing import Dict, Any, Optional
from config import (
    VLLM_API_URL, VLLM_MODELS_URL, MODEL_NAME,
    MAX_NEW_TOKENS_FAST, MAX_NEW_TOKENS_SLOW,
    TEMPERATURE_FAST, TEMPERATURE_SLOW, TOP_P
)
from core.prompts import SELF_EVAL_PROMPT_ZH, FAST_THINKING_PROMPT_ZH


class InferenceEngine:
    """推理引擎，支持快思考和慢思考两种模式"""
    
    def __init__(
        self,
        api_url: str = VLLM_API_URL,
        model_name: str = MODEL_NAME
    ):
        self.api_url = api_url
        self.model_name = model_name
        self.headers = {"Content-Type": "application/json"}
        
        # 检查服务可用性
        self._check_service()
    
    def _check_service(self):
        """检查vLLM服务是否可用"""
        try:
            models_url = VLLM_MODELS_URL
            resp = requests.get(models_url, timeout=5)
            if resp.status_code == 200:
                print(f"✓ vLLM service is ready at {self.api_url}")
            else:
                print(f"⚠ vLLM service returned status {resp.status_code}")
        except Exception as e:
            raise RuntimeError(
                f"Could not connect to vLLM service at {self.api_url}. "
                f"Please ensure service is running. Error: {e}"
            )
    
    def infer_fast(self, data_item: Any) -> str:
        """
        快思考推理
        - 较低的温度参数，更确定性的输出
        - 较短的生成长度
        - 直接回答问题
        """
        prompt = self._build_fast_prompt(data_item)
        
        response = self._call_vllm(
            prompt=prompt,
            max_tokens=MAX_NEW_TOKENS_FAST,
            temperature=TEMPERATURE_FAST
        )
        
        return response
    
    def infer_slow(self, data_item: Any) -> str:
        """
        慢思考推理
        - 较高的温度参数，允许更多创造性
        - 较长的生成长度
        - 引导模型逐步思考
        """
        prompt = self._build_slow_prompt(data_item)
        
        response = self._call_vllm(
            prompt=prompt,
            max_tokens=MAX_NEW_TOKENS_SLOW,
            temperature=TEMPERATURE_SLOW
        )
        
        return response
    
    def infer_slow_then_fast(self, data_item: Any) -> Dict[str, str]:
        """
        先慢思考后快思考（根据论文建议）
        慢思考的结果可以引导快思考给出更好的答案
        """
        # 第一步：慢思考，进行详细推理
        slow_response = self.infer_slow(data_item)
        
        # 第二步：基于慢思考的结果，用快思考给出简洁答案
        fast_prompt = self._build_fast_from_slow_prompt(data_item, slow_response)
        
        fast_response = self._call_vllm(
            prompt=fast_prompt,
            max_tokens=MAX_NEW_TOKENS_FAST,
            temperature=TEMPERATURE_FAST
        )
        
        return {
            "slow_thinking": slow_response,
            "fast_answer": fast_response
        }
    
    def self_evaluate(self, data_item: Any, fast_response: str) -> Dict[str, str]:
        """
        元认知自我评估 (创新点二)
        评估快思考结果的可靠性
        """
        question = data_item.prompt or data_item.question
        prompt = SELF_EVAL_PROMPT_ZH.format(
            question=question,
            fast_response=fast_response
        )
        
        eval_output = self._call_vllm(
            prompt=prompt,
            max_tokens=200,
            temperature=TEMPERATURE_FAST
        )
        
        # 解析标签
        label = "Uncertain"  # 默认值
        if "[[Confident]]" in eval_output:
            label = "Confident"
        elif "[[Incorrect]]" in eval_output:
            label = "Incorrect"
        elif "[[Uncertain]]" in eval_output:
            label = "Uncertain"
            
        return {
            "label": label,
            "reason": eval_output.replace(f"[[{label}]]", "").strip()
        }

    def infer_dynamic(self, data_item: Any) -> Dict[str, Any]:
        """
        动态认知路由 (AgentV3 核心逻辑)
        Fast -> Evaluate -> Slow (if needed)
        """
        # 1. 快思考
        fast_response = self.infer_fast(data_item)
        
        # 2. 自我评估
        eval_result = self.self_evaluate(data_item, fast_response)
        
        # 3. 动态路由决策
        is_slow_triggered = False
        final_answer = fast_response
        slow_thinking = None
        
        if eval_result["label"] in ["Uncertain", "Incorrect"]:
            is_slow_triggered = True
            # 触发慢思考
            slow_result = self.infer_slow_then_fast(data_item)
            final_answer = slow_result["fast_answer"]
            slow_thinking = slow_result["slow_thinking"]
            
        return {
            "final_answer": final_answer,
            "fast_response": fast_response,
            "slow_thinking": slow_thinking,
            "eval_label": eval_result["label"],
            "eval_reason": eval_result["reason"],
            "is_slow_triggered": is_slow_triggered
        }

    def _build_fast_prompt(self, data_item: Any) -> str:
        """构建快思考的Prompt"""
        lang = data_item.lang
        task_type = data_item.task_type
        question = data_item.prompt or data_item.question
        
        if lang == "zh":
            if task_type == "question_answering":
                return f"请直接回答以下问题：\n\n{question}\n\n答案："
            elif task_type == "automatic_grading":
                return f"请对以下学生答案进行评分：\n\n{question}\n\n评分结果："
            elif task_type == "error_correction":
                return f"请指出以下答案的错误并给出正确答案：\n\n{question}\n\n纠错："
            elif task_type == "idea_prompting":
                return f"请为以下问题提供解题思路：\n\n{question}\n\n思路："
            else:
                return f"请完成以下任务：\n\n{question}\n\n回答："
        else:  # English
            if task_type == "question_answering":
                return f"Answer the following question directly:\n\n{question}\n\nAnswer:"
            elif task_type == "automatic_grading":
                return f"Grade the following student answer:\n\n{question}\n\nGrading:"
            elif task_type == "error_correction":
                return f"Identify errors and provide correct answer:\n\n{question}\n\nCorrection:"
            elif task_type == "idea_prompting":
                return f"Provide solution approach for:\n\n{question}\n\nApproach:"
            else:
                return f"Complete the following task:\n\n{question}\n\nResponse:"
    
    def _build_slow_prompt(self, data_item: Any) -> str:
        """构建慢思考的Prompt"""
        lang = data_item.lang
        task_type = data_item.task_type
        question = data_item.prompt or data_item.question
        
        if lang == "zh":
            if task_type == "question_answering":
                return f"请逐步分析并回答以下问题：\n\n{question}\n\n让我们一步一步思考：\n"
            elif task_type == "automatic_grading":
                return f"请详细分析并评分以下学生答案：\n\n{question}\n\n评分分析：\n1. 首先分析答案的优点\n2. 然后指出不足\n3. 最后给出评分和建议\n\n"
            elif task_type == "error_correction":
                return f"请仔细分析以下答案的错误：\n\n{question}\n\n纠错分析：\n1. 识别错误之处\n2. 解释为什么错误\n3. 给出正确答案\n\n"
            elif task_type == "idea_prompting":
                return f"请为以下问题提供详细的解题思路：\n\n{question}\n\n解题思路：\n1. 问题分析\n2. 解题步骤\n3. 关键点提示\n\n"
            elif task_type == "personalized_content":
                return f"请根据学生画像设计个性化学习内容：\n\n{question}\n\n设计思路：\n1. 分析学生特点\n2. 确定学习目标\n3. 设计学习内容\n\n"
            elif task_type == "personalized_learning":
                return f"请为学生规划个性化学习路径：\n\n{question}\n\n规划思路：\n1. 评估当前水平\n2. 设定学习目标\n3. 安排学习路径\n\n"
            elif task_type == "question_generation":
                return f"请根据知识点生成高质量题目：\n\n{question}\n\n生成思路：\n1. 分析知识点\n2. 设计题目类型\n3. 编写题目和答案\n\n"
            elif task_type == "teaching_material":
                return f"请设计教学素材：\n\n{question}\n\n设计思路：\n1. 教学目标\n2. 重点难点\n3. 活动设计\n\n"
            else:
                return f"请详细分析并完成以下任务：\n\n{question}\n\n分析过程：\n"
        else:  # English
            if task_type == "question_answering":
                return f"Let's think step by step to answer:\n\n{question}\n\nStep-by-step thinking:\n"
            elif task_type == "automatic_grading":
                return f"Analyze and grade the student answer in detail:\n\n{question}\n\nGrading analysis:\n1. Strengths\n2. Weaknesses\n3. Grade and suggestions\n\n"
            elif task_type == "error_correction":
                return f"Carefully analyze the errors:\n\n{question}\n\nError analysis:\n1. Identify errors\n2. Explain why\n3. Provide correction\n\n"
            elif task_type == "idea_prompting":
                return f"Provide detailed solution approach:\n\n{question}\n\nApproach:\n1. Problem analysis\n2. Solution steps\n3. Key points\n\n"
            else:
                return f"Analyze and complete the task in detail:\n\n{question}\n\nAnalysis:\n"
    
    def _build_fast_from_slow_prompt(self, data_item: Any, slow_response: str) -> str:
        """基于慢思考结果构建快思考Prompt"""
        lang = data_item.lang
        question = data_item.prompt or data_item.question
        
        if lang == "zh":
            return f"""基于以下详细分析，请给出简洁的最终答案：

问题：
{question}

详细分析：
{slow_response}

请根据上述分析，直接给出最终答案（简洁明了）：
"""
        else:
            return f"""Based on the detailed analysis below, provide a concise final answer:

Question:
{question}

Detailed Analysis:
{slow_response}

Final Answer (concise):
"""
    
    def _call_vllm(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """调用vLLM API"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": TOP_P
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=120  # 2分钟超时
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['text'].strip()
        except requests.exceptions.Timeout:
            print(f"⚠ Request timeout for prompt: {prompt[:50]}...")
            return "[ERROR: Request timeout]"
        except Exception as e:
            print(f"⚠ Error in vLLM inference: {e}")
            return f"[ERROR: {str(e)}]"


if __name__ == "__main__":
    # 测试推理引擎
    from data_loader import DataItem
    
    # 创建测试数据
    test_item = DataItem(
        task_type="question_answering",
        prompt="1+1等于多少？",
        question="1+1等于多少？",
        subject="数学",
        education_level="小学",
        question_type="单选题",
        lang="zh"
    )
    
    try:
        engine = InferenceEngine()
        
        print("="*60)
        print("测试快思考：")
        print("="*60)
        fast_result = engine.infer_fast(test_item)
        print(fast_result)
        
        print("\n" + "="*60)
        print("测试慢思考：")
        print("="*60)
        slow_result = engine.infer_slow(test_item)
        print(slow_result)
        
    except RuntimeError as e:
        print(f"\n错误: {e}")
        print("请确保vLLM服务已启动！")
