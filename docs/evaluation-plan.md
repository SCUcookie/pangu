# Evaluate Plan: AgentV3 vs. EduBench

## 1. Purpose
The primary objective of this evaluation is to empirically validate the effectiveness of the **AgentV3** architecture—specifically the **Meta-Cognitive Feedback-driven Dynamic Thinking** approach—against the baseline **AgentV2** (static rule-based) and **industry-standard SOTA models** published in the EduBench paper. We aim to prove that dynamic scheduling based on self-evaluation improves accuracy and resource efficiency (latency) in complex educational scenarios, reaching or exceeding the performance of specialized educational models.

## 2. Approach: AgentV3 "Cognitive Router"
The evaluation will compare three levels of performance:
- **Baseline (AgentV2)**: Uses static rules (subject, education level, keywords) to decide between Fast or Slow thinking.
- **Proposed (AgentV3)**: Implements a "Cognitive Router" pipeline:
    1. **Task Identification**: Detect task type (Q&A, AG, EC, etc.).
    2. **Fast Thinking**: Execute a quick response using a task-specific `FAST_PROMPT`.
    3. **Meta-Cognitive Evaluation**: The model evaluates its own fast response (Confident, Uncertain, or Incorrect).
    4. **Dynamic Routing**: 
        - If `Confident` -> Output Fast Answer.
        - If `Uncertain/Incorrect` -> Trigger Slow Thinking with `SLOW_PROMPT` (Chain-of-Thought).
- **External Benchmarks (EduBench Paper)**: Compare results against reported scores for:
    - **GPT-4o** (Original Paper Evaluator)
    - **DeepSeek R1 / V3**
    - **Qwen2.5-7B/14B-Instruct**

## 3. Evaluation Setup

### 3.1 Dataset: EduBench (Full/Subset)
We will use the Chinese subset (`zh_data`) of EduBench, covering 8-9 core educational tasks:
- **Student-Oriented**: Q&A, Error Correction (EC), Idea Provision (IP), Personalized Learning (PLS), Emotional Support (ES).
- **Teacher-Oriented**: Question Generation (QG), Automatic Grading (AG), Teaching Material (TMG), Personalized Content (PCC).

### 3.2 Metrics & Evaluator
We will transition from internal evaluation to a high-standard API-based judge to ensure comparability with the original paper.
1. **Evaluator**: **GPT-5.4 API** (upgraded from GPT-4o used in the paper) will serve as the "Model-as-a-Judge".
2. **Accuracy (Acc)**: 1-10 scale scoring across the 12 core evaluation indicators (Scenario Adaptability, Factual Accuracy, Pedagogical Application).
3. **Slow Trigger Rate (STR)**: The percentage of cases where the meta-cognitive module invoked slow thinking (efficiency metric).
4. **Average Latency**: Time taken per request (seconds).

## 4. Detailed Implementation Plan (Steps)

### Step 1: Baseline Execution (AgentV2)
- Run the existing `main.py` on the sampled EduBench dataset.
- Record results in `outputs/results/baseline_v2.jsonl`.
- Calculate baseline Acc, STR (based on rules), and Latency.

### Step 2: System Upgrade to AgentV3
- **Prompt Engineering**: Create `prompt_manager.py` with templates for all EduBench scenarios.
- **Meta-Cognitive Implementation**: Modify `inference_engine.py` to include the `self_evaluate` method.
- **Cognitive Router**: Update `main.py` (or a new `agent_v3.py`) to implement the "Fast -> Evaluate -> Slow" logic.

### Step 3: Experimental Execution (AgentV3)
- Run AgentV3 on the **same** dataset.
- Record results in `outputs/results/proposed_v3.jsonl`.

### Step 4: Comparative Analysis & Benchmarking
- Use a dedicated evaluation script to:
    - Compare Accuracy (AgentV3 vs. AgentV2).
    - **Benchmarking**: Compare AgentV3 scores against Table 1 and Table 2 from the EduBench paper (DeepSeek R1, GPT-4o results).
    - Analyze the correlation between Meta-Cognitive labels and actual correctness.
    - Measure the efficiency gain (Latency vs. Accuracy trade-off).

### Step 5: Final Report
- Generate a summary table comparing AgentV2, AgentV3, and Paper Baselines.
- Document qualitative examples where meta-cognition successfully corrected a "fast" error.

---
**Status**: Planning Phase Updated with External Benchmarks. Ready for Implementation.
