# Experiment Log — AD Multiagent Evaluation

Date: 2026-05-06

## 目标
- 将 demo 演进为医疗多智能体 AD 会诊（可重复、可审计、结构化 JSON 输出）。
- 严格 JSON 合约字段：`final_judgment`, `risk_level`, `recommended_tests`, `disagreement_points`, `next_steps`, `safety_notes`, `evidence_chunks`。

## 当前基线（8/8 检查项）
- 1) 提交基线（commit 当前 8/8）：未提交（需用户执行 git commit）。
- 2) 文档 `docs/experiment_log.md`：已创建（此文件）。
- 3) `run_eval_cases.py` 添加 summary 输出：已完成（写入 `tests/eval_summary.json`）。
- 4) `run_eval_cases.py` 支持 case 筛选/limit/repeat：已完成（`--case-id`, `--limit`, `--repeat`）。
- 5) 中间结果缓存：已实现（`--use-cache`, `--force`，缓存文件 `tests/eval_cache.json`）。
- 6) 扩展测试集到 20 条：未完成（现有 `tests/ad_eval_cases.json` 需扩展）。
- 7) 只在关键节点全量跑：未实现（建议在 CI 或脚本中控制）。
- 8) FAISS/Chroma/微调：规划中（后续专题）。

## 最近动作摘要
- 清理 `agents.yaml`，把 LLM 注入移至 `crew.py`（temperature=0，减少随机性）。
- 加强 `tasks.yaml` 中的合成规则（MoCA/病历锚定、情绪/睡眠规则）。
- `run_eval_cases.py` 增加重复运行、解析容错、summary 输出，并实现本地缓存以减少重复 API 调用。

## 建议的下步执行（最小可行）
1. 在本地把当前修改 `git add . && git commit -m "chore: AD eval baseline v0 — summary, repeat, cache, tasks tweaks"`。
2. 在 `run_eval_cases.py` 中实现中间结果缓存（已完成）。
3. 扩展 `tests/ad_eval_cases.json` 到 20 条（可分批补充并通过小规模 run 校验）。
4. 添加 CI 作业或脚本控制全量运行时机（merge 到 main / release 标签触发）。

## 变更日志（简要）
- 2026-05-06: 注入 shared LLM（temperature=0）；添加 `--repeat` 与 summary；实现缓存 `--use-cache`。

