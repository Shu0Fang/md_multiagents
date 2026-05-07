# Experiment Log

## 1. Project Goal

本项目探索基于 CrewAI 的医学多智能体协作流程，在阿尔茨海默病/认知下降风险评估场景中，结合指南知识库，生成结构化、可追溯的初步风险分层和检查建议。

## 2. System Version

### v0.1: Initial AD Multi-agent MVP
- 将原始 CrewAI demo 改造为 AD 多智能体会诊流程。
- 流程包括：
  - extraction_task
  - primary_care_task
  - neurologist_task
  - geriatrician_task
  - psychiatrist_task
  - psychologist_task
  - synthesis_task

### v0.2: Structured Output
- 所有 task 输出 JSON object。
- 增加 risk_level、recommended_tests、next_steps、safety_notes、evidence_chunks 等字段。

### v0.3: Keyword RAG
- 将《中国阿尔茨海默病痴呆诊疗指南（2020）》转换为 txt。
- 清洗并切分为 knowledge/ad_chunks。
- 实现 RagTool 关键词检索。
- 专科 agent 和 synthesis agent 挂载 RagTool。

### v0.4: Evaluation Workflow
- 创建 tests/ad_eval_cases.json。
- 实现 run_eval_cases.py。
- 支持 case-id、limit、repeat、cache、summary。
- 建立 8-case baseline。

## 3. Baseline Evaluation

### 8-case baseline
- 覆盖典型 AD、MCI、抑郁相关认知下降、血管性认知障碍、可逆病因、信息不足、快速进展、正常老化。
- 最终 risk_level accuracy: 8/8。

### 20-case extended evaluation
- 总 case 数：20
- 通过数：14
- 失败数：6
- accuracy: 0.70

## 4. Failure Analysis

失败 case:
- AD-009：早发 + 强家族史，expected high，predicted medium。
- AD-010：DLB 特征，expected high，predicted medium。
- AD-012：NPH 三联征，expected high，predicted medium。
- AD-014：药物相关认知下降，expected low，predicted medium。
- AD-016：听力/视力下降干扰，expected low，predicted medium。
- AD-019：病历内部矛盾，expected insufficient，predicted medium。

主要问题：
- 对 DLB / NPH 等非典型但高风险模式覆盖不足。
- 对药物、感官障碍等可逆/混杂因素仍偏保守。
- 对病历内部矛盾的处理不够严格。
- 当前问题主要在 synthesis 风险边界和冲突处理，而不是 RAG 检索或 JSON 解析。

## 5. Current Limitations

- 测试集为人工构造模拟病例，不代表真实临床性能。
- RAG 仍为关键词检索，尚未升级为向量检索。
- 风险分级规则仍依赖 prompt，存在边界波动。
- 多智能体调用成本较高。
- 未进行真实临床验证，不能用于实际诊断。

## 6. Next Steps

- 人工复核 AD-009、AD-016、AD-019 的 expected label。
- 增加通用规则：
  - DLB 高风险模式
  - NPH 高风险/可治疗认知障碍模式
  - 病历冲突 → insufficient
  - 药物/感官障碍优先排查规则
- 扩展更多 DLB、NPH、药物、感官障碍和信息冲突病例。
- 后续考虑中间结果缓存、向量 RAG、模型分层调用。

## 2026-05-07 v0.5 扩展测试集评测

### 做了什么
- 新增/使用 20 条扩展测试 case。
- 覆盖 DLB、NPH、药物相关、感官障碍、信息冲突等边界场景。
- 使用当前 CrewAI + keyword RAG + structured JSON 流程进行评测。

### 结果
- 总 case 数：20
- 通过数：14
- accuracy：0.70
- error_count：0
- evidence_chunks 均非空

### 发现的问题
- DLB / NPH 等非 AD 高风险模式容易被判为 medium。
- 药物相关、听力/视力干扰病例容易被抬到 medium。
- 病历内部矛盾病例没有稳定判为 insufficient。
- 主要问题在风险规则和 synthesis 汇总逻辑，不是 API/JSON/RAG 链路故障。

### 下一步
- 先人工复核 AD-009、AD-016、AD-019 的 expected label。
- 再考虑补充 DLB、NPH、病历冲突等通用规则。
- 暂时不做 FAISS / 微调。
- 下一步将补充通用分层规则，而不是针对单个病例硬编码。

