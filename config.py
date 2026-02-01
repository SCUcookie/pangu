"""
配置文件 - AgentV2
包含模型路径、数据集路径、推理参数等配置
"""
import os

# 模型配置
MODEL_PATH = "/opt/pangu/openPangu-Embedded-7B-V1.1"
MODEL_NAME = "pangu_embedded_7b"

# vLLM 服务配置
VLLM_API_URL = "http://172.17.0.1:8000/v1/completions"
VLLM_MODELS_URL = "http://172.17.0.1:8000/v1/models"

# 数据集路径
DATA_DIR = "/opt/pangu/ldh/EduBench/data/all_data"
ZH_DATA_DIR = os.path.join(DATA_DIR, "zh_data")
EN_DATA_DIR = os.path.join(DATA_DIR, "en_data")

# 输出路径
OUTPUT_DIR = "/opt/pangu/ldh/agentv2/results"

# 推理参数
MAX_NEW_TOKENS_FAST = 512      # 快思考最大生成token数
MAX_NEW_TOKENS_SLOW = 2048     # 慢思考最大生成token数
TEMPERATURE_FAST = 0.3         # 快思考温度（更确定性）
TEMPERATURE_SLOW = 0.7         # 慢思考温度（更有创造性）
TOP_P = 0.9

# 调试模式
DEBUG_MODE = True
DEBUG_SAMPLE_SIZE = 3  # 调试模式下每种任务类型的样本数

# 任务类型映射
TASK_TYPES = {
    "Q&A": "question_answering",      # 问答
    "AG": "automatic_grading",        # 自动评分
    "EC": "error_correction",         # 纠错
    "IP": "idea_prompting",           # 思路提示
    "PCC": "personalized_content",    # 个性化学习内容
    "PLS": "personalized_learning",   # 个性化学习方案
    "QG": "question_generation",      # 题目生成
    "TMG": "teaching_material",       # 教学素材生成
    "ES": "essay_scoring",            # 作文评分
}

# 难度关键词（用于难度感知）
DIFFICULTY_KEYWORDS = {
    "easy": ["小学", "基础", "简单", "初级", "elementary", "basic", "simple", "primary"],
    "medium": ["中学", "中等", "初中", "middle", "intermediate", "secondary"],
    "hard": ["高中", "高级", "困难", "复杂", "大学", "高等", "high school", "advanced", "complex", "university"]
}

# 学科关键词
SUBJECT_KEYWORDS = {
    "math": ["数学", "数", "计算", "方程", "几何", "math", "calculate", "equation", "geometry"],
    "physics": ["物理", "力学", "电学", "physics", "mechanics", "electricity"],
    "chemistry": ["化学", "元素", "反应", "chemistry", "element", "reaction"],
    "chinese": ["语文", "汉语", "文言文", "作文", "chinese", "writing", "literature"],
    "english": ["英语", "英文", "english", "grammar"],
    "other": []
}

# ============================================================
# 以下为Agent后端服务新增配置
# ============================================================

# API服务配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8080"))
API_PREFIX = "/api/v1"
CORS_ORIGINS = ["*"]

# 数据库配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'agentv2.db')}")
DATABASE_ECHO = False  # SQL日志，调试时可设为True

# 会话配置
SESSION_EXPIRE_HOURS = 24
SESSION_MAX_MESSAGES = 100
SESSION_TITLE_MAX_LENGTH = 50

# 记忆配置
MEMORY_MAX_MESSAGES = 20
MEMORY_MAX_TOKENS = 4096
MEMORY_COMPRESSION_THRESHOLD = 0.8

# 工具配置
TOOL_TIMEOUT_SECONDS = 30
TOOL_MAX_RETRIES = 2
ENABLED_TOOLS = ["calculator", "knowledge", "formula_lookup"]

# Agent配置
AGENT_MAX_TOOL_CALLS = 3
AGENT_TOOL_DETECTION_KEYWORDS = {
    "calculator": ["计算", "等于", "求", "算", "calculate", "compute", "="],
    "knowledge": ["什么是", "解释", "定义", "what is", "explain", "define"],
    "formula_lookup": ["公式", "定理", "formula", "theorem"]
}
