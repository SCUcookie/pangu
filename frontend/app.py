import streamlit as st
import requests
import json
import os
import sys
import time
from datetime import datetime

# page config
st.set_page_config(
    page_title="盘古教育Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 添加父目录到 sys.path 以便导入配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 默认配置
DEFAULT_API_URL = "http://localhost:8080/api/v1"
DEFAULT_TASK_TYPES = {
    "Q&A": "question_answering",
    "AG": "automatic_grading",
    "EC": "error_correction",
    "IP": "idea_prompting",
    "PCC": "personalized_content",
    "PLS": "personalized_learning",
    "QG": "question_generation",
    "TMG": "teaching_material",
    "ES": "essay_scoring",
}

try:
    from config import API_HOST, API_PORT, API_PREFIX, TASK_TYPES
    # 优先使用配置中的 API_HOST, 但如果是 0.0.0.0, 替换为 localhost 方便前端访问
    host = API_HOST
    if host == "0.0.0.0":
        host = "localhost"
    API_URL = f"http://{host}:{API_PORT}{API_PREFIX}"
except ImportError:
    # 如果导入失败，使用默认值
    API_URL = DEFAULT_API_URL
    TASK_TYPES = DEFAULT_TASK_TYPES

st.title("🎓 盘古教育Agent")

# 初始化 Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "metrics" not in st.session_state:
    st.session_state.metrics = {"latency": [], "tokens": []}

# Sidebar 配置
with st.sidebar:
    st.header("⚙️ 设置")

    # 任务类型选择
    st.subheader("任务配置")
    selected_task_label = st.selectbox(
        "任务类型",
        options=list(TASK_TYPES.keys()),
        format_func=lambda x: f"{x} ({TASK_TYPES[x]})",
        index=0,
        help="选择Agent处理的任务类型"
    )
    task_type = TASK_TYPES[selected_task_label]

    # 上下文设置
    st.subheader("上下文信息")
    subject = st.text_input("📚 学科", value="数学")
    education_level = st.selectbox(
        "🎓 教育阶段",
        ["小学", "初中", "高中", "大学", "成人"],
        index=1
    )

    st.markdown("---")
    
    # 统计信息展示
    st.subheader("📊 实时指标")
    if st.session_state.metrics["latency"]:
        avg_latency = sum(st.session_state.metrics["latency"]) / len(st.session_state.metrics["latency"])
        total_tokens = sum(st.session_state.metrics["tokens"])
        
        col1, col2 = st.columns(2)
        col1.metric("平均延迟", f"{avg_latency:.0f}ms")
        col2.metric("Token消耗", f"{total_tokens}")
        
        # 简单趋势图
        st.caption("延迟趋势 (ms)")
        st.line_chart(st.session_state.metrics["latency"])
    else:
        st.info("暂无对话数据")

    st.markdown("---")

    # 清除历史
    if st.button("🗑️ 清除对话历史", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.session_state.metrics = {"latency": [], "tokens": []}
        st.rerun()

# 主界面：聊天区域
chat_container = st.container()

# 显示聊天历史
with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        #### 👋 欢迎使用盘古教育Agent！
        
        您可以尝试问我：
        - "请帮我出一道初中数学的一次函数题目"
        - "解释一下牛顿第一定律"
        - "批改这篇作文：Today is a good day..."
        
        请在左侧设置栏调整任务类型和学科信息。
        """)
    
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # 如果是助手回复且有元数据
            if message["role"] == "assistant" and "metadata" in message:
                with st.expander("ℹ️ 思考过程与详情"):
                    st.write(f"**思考模式**: {message.get('thinking_mode', 'N/A')}")
                    if "latency" in message:
                         st.write(f"**耗时**: {message['latency']:.0f}ms")
                    st.json(message["metadata"])

# 处理用户输入
if prompt := st.chat_input("请输入您的问题..."):
    # 构造请求 payload
    payload = {
        "user_id": "streamlit_user",  # 简化 user_id
        "session_id": st.session_state.session_id,
        "message": prompt,
        "task_type": task_type,
        "context": {
            "subject": subject,
            "education_level": education_level
        }
    }

    # 1. 展示用户输入
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 调用 API 并展示结果
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.status("🤖 Agent 正在思考中...", expanded=True)
        
        start_time = time.time()
        try:
            response = requests.post(f"{API_URL}/chat", json=payload)
            response.raise_for_status()
            result = response.json()
            end_time = time.time()
            
            # 更新 Session ID
            new_session_id = result.get("session_id")
            if new_session_id:
                st.session_state.session_id = new_session_id
            
            assistant_response = result.get("response", "无响应内容")
            thinking_mode = result.get("thinking_mode", "unknown")
            metadata = result.get("metadata", {})
            
            # 记录指标
            latency = (end_time - start_time) * 1000
            tokens = metadata.get("tokens_used", 0)
            
            # 更新 metrics
            st.session_state.metrics["latency"].append(latency)
            st.session_state.metrics["tokens"].append(tokens)
            
            status_placeholder.update(label="完成!", state="complete", expanded=False)
            
            # 展示回复
            message_placeholder.markdown(assistant_response)
            
            # 展示元数据
            with st.expander("ℹ️ 思考过程与详情"):
                st.write(f"**思考模式**: {thinking_mode}")
                st.write(f"**耗时**: {latency:.0f}ms")
                st.json(metadata)
            
            # 保存到历史
            st.session_state.messages.append({
                "role": "assistant", 
                "content": assistant_response,
                "thinking_mode": thinking_mode,
                "metadata": metadata,
                "latency": latency
            })
            
        except requests.exceptions.RequestException as e:
            status_placeholder.update(label="请求失败", state="error", expanded=False)
            message_placeholder.markdown(f"❌ 请求失败: {str(e)}")
            st.error(f"无法连接到后端 API，请确认服务已启动。\nAPI 地址: `{API_URL}`")
