# Project Overview

Date: 2026-03-13
Active branch: `agentv4`

## 1. What this repo is trying to achieve

This repository is not just a chatbot demo. Its real target is a publishable education agent built on Huawei Pangu Embedded 7B, with a research story around:

- metacognitive routing
- task-specific prompting
- fast/slow reasoning control
- reproducible EduBench evaluation

The objective stated in `docs/purpose.md` is to turn the existing education QA system into a paper-ready agent that can be defended both academically and engineering-wise.

## 2. Where the current branch stands

As of 2026-03-13, the local branch layout is:

- `main`: initial Pangu LLM scaffold
- `frontend-optimization`: frontend-focused iteration
- `agentv3`: ReAct, tool use, and dynamic profiling direction
- `evaluate`: evaluation pipeline plus 4x2 parallel inference
- `agentv4`: local cleanup branch, currently aligned with commit `5f30237`

That means `agentv4` is the right place to continue, because it already contains the evaluation additions from `evaluate` and now has a cleaner directory layout.

## 3. Code structure after cleanup

- `api/`: FastAPI app, routes, schemas, dependency wiring
- `core/`: agent loop, prompts, memory, tool registry
- `db/`: SQLAlchemy setup and models
- `frontend/`: Streamlit interface for interactive testing
- `services/`: session and profile logic
- `scripts/`: operational scripts for vLLM, Docker, and frontend launch
- `docs/`: research notes, purpose, and evaluation plan
- `outputs/results/`: generated evaluation outputs
- `runtime/`: local-only state such as SQLite, logs, and secrets

## 4. What is still mixed conceptually

The repository is cleaner structurally now, but the implementation still has a version-name mismatch:

- branch name: `agentv4`
- many code symbols/docs: `AgentV3`

This is only naming debt. It does not block the next step, but it is worth cleaning when you start the next actual algorithm iteration.

## 5. Recommended next step on agentv4

To support the paper direction in `docs/purpose.md`, the next implementation pass should focus on:

1. extract a dedicated `prompt_manager.py` for task-specific fast/slow templates
2. separate the cognitive router logic from the raw inference client
3. define one stable experiment entrypoint for baseline vs proposed runs
4. standardize result schemas so paper tables can be generated directly from `outputs/results/`
