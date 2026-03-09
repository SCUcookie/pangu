# AgentV2 - 华为盘古模型教育解题高级Agent

基于华为盘古嵌入式7B模型的教育问答系统，支持快慢思考机制、用户画像、历史记忆和工具调用。

## 功能特点

1. **模块化架构**：不同功能分离到独立模块
2. **难度感知决策**：自动判断题目难度，选择快思考或慢思考
3. **多任务支持**：支持8种不同类型的教育任务
4. **多语言支持**：支持中文和英文数据集
5. **灵活的数据加载**：自动适配不同格式的jsonl文件
6. **🆕 RESTful API服务**：基于FastAPI的HTTP接口
7. **🆕 用户画像**：记录学习水平、偏好、薄弱点
8. **🆕 会话管理**：支持多轮对话和历史记忆
9. **🆕 工具调用**：内置计算器、公式查询、知识查询工具
10. **🆕 可视化前端**：基于Streamlit的Web交互界面，支持实时对话、参数配置与思考过程展示

## 目录结构

```
agentv2/
├── api/                     # FastAPI服务层
│   ├── main.py             # 应用入口
│   ├── dependencies.py     # 依赖注入
│   ├── routes/             # 路由定义
│   └── schemas/            # Pydantic模型
├── core/                    # 核心Agent逻辑
│   ├── agent.py            # Agent核心控制器
│   ├── context.py          # 上下文数据类
│   ├── prompts.py          # 提示词模板
│   ├── memory/             # 记忆管理
│   └── tools/              # 工具系统
├── db/                      # 数据持久化
│   ├── database.py         # 数据库连接
│   ├── models.py           # SQLAlchemy模型
│   └── crud.py             # CRUD操作
├── services/                # 业务服务层
│   ├── user_profile.py     # 用户画像服务
│   └── session_manager.py  # 会话管理服务
├── config.py                # 配置文件
├── data_loader.py           # 数据加载器
├── difficulty_decision.py   # 难度感知决策模块
├── inference_engine.py      # 推理引擎
├── main.py                  # 批处理主程序
├── run_server.py            # API服务启动脚本
├── run_frontend.sh          # 前端启动脚本
├── frontend/                # Streamlit前端应用
└── results/                 # 输出结果目录
```

## 快速开始

### 方式一：API服务模式（推荐）

#### 1. 安装依赖

```bash
cd /opt/pangu/ldh/agentv2
pip install -r requirements.txt
```

#### 2. 确保vLLM服务已启动

```bash
cd /opt/pangu/ldh
bash service.sh
```

#### 3. 启动API服务

```bash
cd /opt/pangu/ldh/agentv2
python run_server.py
# 或
uvicorn api.main:app --host 0.0.0.0 --port 8080
```

#### 4. 调用API

```bash
# 发送对话请求
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "请帮我解答：1+1等于多少？",
    "task_type": "question_answering"
  }'

# 查看可用工具
curl http://localhost:8080/api/v1/tools

# 健康检查
curl http://localhost:8080/api/v1/health
```

### 方式二：批处理模式

```bash
cd /opt/pangu/ldh/agentv2
python main.py
```

### 方式三：前端交互模式（Web UI）

此模式提供可视化网页界面，方便用户直接与 Agent 交互。

**前提**：需确保后端 API 服务（方式一）已启动且监听在 `http://localhost:8080`。

```bash
# 1. 启动前端应用
cd /opt/pangu/ldh/agentv2
bash run_frontend.sh

# 2. 浏览器访问
# http://localhost:8501
```

**前端功能**：
- **场景配置**：侧边栏通过下拉框选择任务类型（如问答、作文评分等）及教育背景。
- **对话交互**：支持多轮对话，实时流式体验。
- **思考可视**：可展开查看 Agent 的"快/慢思考"决策过程及元数据（延迟、Token消耗）。


结果保存在 `results/` 目录下。

## API文档

启动服务后访问：
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

### 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/chat | 发送消息获取回复 |
| GET | /api/v1/user/{user_id} | 获取用户画像 |
| GET | /api/v1/session/{session_id} | 获取会话历史 |
| GET | /api/v1/tools | 列出可用工具 |
| POST | /api/v1/tools/invoke | 调用工具 |
| GET | /api/v1/health | 健康检查 |

## 配置说明

编辑 `config.py` 修改配置：

```python
# 调试模式：True=只处理少量样本，False=处理全部数据
DEBUG_MODE = True
DEBUG_SAMPLE_SIZE = 3

# 推理参数
MAX_NEW_TOKENS_FAST = 512      # 快思考最大token数
MAX_NEW_TOKENS_SLOW = 2048     # 慢思考最大token数
TEMPERATURE_FAST = 0.3         # 快思考温度（更确定性）
TEMPERATURE_SLOW = 0.7         # 慢思考温度（更有创造性）
```

## 支持的任务类型

1. **Q&A**: 问答题
2. **AG**: 自动评分
3. **EC**: 纠错
4. **IP**: 思路提示
5. **PCC**: 个性化学习内容
6. **PLS**: 个性化学习方案
7. **QG**: 题目生成
8. **TMG**: 教学素材生成

## 快慢思考决策机制

系统根据以下因素自动决策：

1. **教育水平**：小学→快思考，高中/大学→慢思考
2. **题目长度**：短题目→快思考，长题目→慢思考
3. **题目类型**：单选题→快思考，解答题→慢思考
4. **任务类型**：简单问答→自适应，评分/生成→慢思考

决策结果：
- `fast`: 仅使用快思考
- `slow`: 仅使用慢思考
- `both`: 先慢思考（详细推理），再快思考（简洁答案）

## 测试单个模块

### 测试数据加载器
```bash
python3 data_loader.py
```

### 测试难度决策器
```bash
python3 difficulty_decision.py
```

### 测试推理引擎
```bash
python3 inference_engine.py
```

## 输出格式

每条结果包含以下字段：

```json
{
  "task_type": "question_answering",
  "question": "问题内容",
  "subject": "数学",
  "education_level": "小学",
  "decision": "both",
  "prediction_slow": "详细推理过程...",
  "prediction_fast": "简洁答案",
  "ground_truth": "标准答案"
}
```

## 根据论文实现的特性

1. **快慢思考分离**：不同的prompt策略和参数设置
2. **先慢后快**：用慢思考引导快思考产生更好的答案
3. **自适应决策**：根据任务特征自动选择合适的推理模式

## 注意事项

1. 首次运行建议开启 `DEBUG_MODE=True`，测试少量数据
2. 确保vLLM服务正常运行，否则会报连接错误
3. 大规模推理时间较长，建议使用后台运行：`nohup python3 main.py > run.log 2>&1 &`
