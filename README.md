# Pangu Agent Workspace

`agentv4` 是当前整理后的工作分支，用于继续推进你的论文型教育 Agent。代码里仍保留 `AgentV3` 命名，但这个分支的目标已经明确为下一阶段的研究起点，而不是继续堆叠临时文件。

## 研究目标

你的目标不是做一个普通问答 Demo，而是基于华为盘古嵌入式 7B，做出一个:

- 可写论文的教育 Agent
- 可复现实验的评测系统
- 可在面试中讲清楚设计权衡的工程项目

当前主线是 `Fast Thinking -> Self-Evaluation -> Slow Thinking` 的元认知动态路由，并围绕 EduBench 做准确率、慢思考触发率和延迟分析。

## 当前结构

```text
/opt/pangu/pangu
├── api/               # FastAPI 接口层
├── core/              # Agent 核心逻辑、Prompt、工具与记忆
├── db/                # SQLAlchemy 模型与数据库初始化
├── frontend/          # Streamlit 前端
├── services/          # 会话管理、用户画像等服务
├── docs/              # 研究目标、评测计划、项目概览
├── scripts/           # 启动与部署脚本
├── outputs/results/   # 评测输出与实验结果
├── runtime/           # 本地数据库、日志、密钥
├── config.py          # 全局路径与运行配置
├── data_loader.py     # EduBench 数据加载
├── difficulty_decision.py
├── evaluator.py       # GPT Judge 评测
├── inference_engine.py
├── main.py            # 单实例评测入口
├── main_parallel.py   # 4x2 并行评测入口
└── run_server.py      # API 服务入口
```

## Branch 状态

截至 2026-03-13，`/opt/pangu/pangu` 的分支线大致如下:

- `main`: 初始盘古教育系统骨架
- `frontend-optimization`: 前端早期迭代
- `agentv3`: ReAct 工具链与动态画像版本
- `evaluate`: 加入评测与 4x2 并行推理
- `agentv4`: 当前本地整理分支，提交点与 `evaluate` 同步，作为下一阶段工作的起点

## 运行方式

启动单实例 vLLM:

```bash
cd /opt/pangu/pangu
bash scripts/run_service_7b.sh
```

启动 4x2 并行 vLLM:

```bash
cd /opt/pangu/pangu
bash scripts/run_service_7b_4x2.sh
```

启动 API:

```bash
cd /opt/pangu/pangu
python run_server.py
```

启动前端:

```bash
cd /opt/pangu/pangu
bash scripts/run_frontend.sh
```

运行评测:

```bash
cd /opt/pangu/pangu
python main.py
python main_parallel.py
```

## 路径约定

- 数据集默认读取 `/opt/pangu/EduBench/data/all_data`
- 实验输出默认写入 `outputs/results/`
- SQLite 默认放在 `runtime/db/agentv2.db`
- 评测密钥优先读取环境变量 `GPT5_API_KEY`，否则读取 `runtime/secrets/GPT-key`

## 文档入口

- `docs/project-overview.md`: 当前分支、模块职责、下一步建议
- `docs/purpose.md`: 你的研究目标与工程约束
- `docs/evaluation-plan.md`: 评测与对比实验计划
