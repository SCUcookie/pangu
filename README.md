# AgentV3 - 科研向教育评测增强 Agent

基于华为盘古嵌入式 7B 模型的高级教育问答与评测系统。本系统 (AgentV3) 专为解决复杂教育场景（如 EduBench 评测集）中的“模型幻觉”和“非个性化解答”问题而设计。

## 🌟 核心创新点 (科研价值)

1. **Tool-Augmented Reasoning (基于 ReAct 的工具增强推理)**
   *   抛弃了传统的单轮推理模式和硬编码规则，实现了 `Thought -> Action -> Action Input -> Observation` 的自主执行循环。
   *   内置了安全的 `PythonSandbox` 和专门针对微积分/代数求解的 `SympySolver`。
   *   大幅提升了模型在涉及复杂数学计算、物理公式推导时的绝对准确率，有效克服了原生大模型易犯的数值幻觉。

2. **Dynamic Profiling & Knowledge Tracking (动态画像与知识追踪)**
   *   利用 SQLAlchemy 建立了细粒度的 `KnowledgeNode`（知识点节点）表。
   *   基于艾宾浩斯遗忘曲线模拟用户在各个微小知识点上的掌握度 (Mastery Level) 衰减。
   *   在每次模型回答前，自动检索并提取该用户最近暴露的“薄弱知识点”和“历史错因”，将其作为自适应 Prompt 注入，实现了千人千面的个性化教学。

## 目录结构 (核心更新部分)

```text
agentv3/
├── api/                     # FastAPI服务层
├── core/                    # 核心Agent逻辑
│   ├── agent.py            # [🔥重构] Agent核心控制器，内置了 ReAct 调度循环
│   ├── prompts.py          # [🔥重构] 支持了工具说明与动态记忆注入的 Prompt
│   └── tools/
│       └── advanced/       # [🆕新增] 科研版核心沙箱工具
│           ├── python_sandbox.py  # 通用安全代码沙箱
│           └── sympy_solver.py    # SymPy 数学符号计算器
├── db/                      
│   └── models.py           # [🔥重构] 增加了 KnowledgeNode 等动态记忆追踪表
├── services/                
│   └── user_profile.py     # [🔥重构] 包含了计算遗忘曲线与生成 Active Memory 的逻辑
└── frontend/                # Streamlit 前端 (可视化思考过程)
```

## 快速启动验证

### 1. 确保 vLLM 服务已启动

确保底层盘古模型的 vLLM 接口可用（默认监听 `http://172.17.0.1:8000/v1/completions`）。

### 2. 启动 API 后端服务

首次运行会自动在当前目录下重建和迁移数据库 `agentv2.db`。

```bash
cd /opt/pangu/pangu
python run_server.py
```
*预期输出: `✓ Agent API服务已启动` 并在 `8080` 端口监听。*

### 3. (可选) 启动可视化前端

打开另一个终端，启动 Streamlit 可视化界面：

```bash
cd /opt/pangu/pangu
bash run_frontend.sh
```
*此时可通过浏览器访问控制台输出的本地端口（通常是 `8501`）进行测试。*

## 实验与评估设计建议 (For Ablation Study)

如果需要在论文中展示效果，可以通过修改 `/opt/pangu/pangu/core/agent.py` 中的开关来进行消融实验：
- **无工具纯思考 (w/o Tools)**: 将 `self.max_react_steps` 设为 0。
- **无动态记忆 (w/o Dynamic Profiling)**: 将 `_init_context` 中获取的 `dynamic_memory` 设为空字符串。
- 随后使用 EduBench 评测集对比不同策略下的回答准确率和生成的 CoT 质量。

---

*旧版 AgentV2 特性（如快慢思考决策树等）已在 V3 中兼容并向下保留。*