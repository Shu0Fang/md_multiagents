# md_multiagents: 基于 CrewAI 的认知障碍风险初筛多智能体原型系统

本项目是一个基于 CrewAI 的医疗多智能体原型系统，面向阿尔茨海默病（Alzheimer's Disease, AD）及相关认知障碍的风险初筛场景。系统以中文自然语言病史为输入，通过“信息提取 + 多专科分析 + 综合判断”的流程，输出结构化 JSON 报告，包括风险等级、推荐检查、下一步处理建议、安全提示和证据来源。

> ⚠️ 本项目仅用于课程/科研训练和原型验证，不构成临床诊断工具，也不能用于真实医疗决策。

---

## 项目特点

- **多智能体协作**：模拟多学科会诊流程，包括全科、神经科、老年医学、精神科、心理学和综合判断智能体。
- **结构化输出**：最终输出统一为 JSON，包含 `risk_level`、`recommended_tests`、`next_steps`、`safety_notes`、`evidence_chunks` 等字段。
- **指南知识库 RAG**：基于《中国阿尔茨海默病痴呆诊疗指南（2020）》构建本地知识库，使用关键词检索提供可追溯依据。
- **Rule Checker**：实现轻量规则辅助模块，用于识别 DLB、NPH、MoCA 边界异常、甲减样表现、药物相关认知下降和病历矛盾等高置信模式。
- **自动化评测**：支持 baseline/extended 测试集、批量评测、单病例测试、summary 输出和 single-agent baseline 对比。

---

## 系统流程

```text
patient_record
  ↓
Data Extraction Agent
  ↓
Primary Care Agent
Neurologist Agent
Geriatrician Agent
Psychiatrist Agent
Psychologist Agent
  ↓
Synthesis Agent
  ↓
Structured JSON Output
````

最终输出示例：

```json
{
  "final_judgment": "患者存在持续进展的近期记忆下降、空间定向障碍和日常生活能力受损，提示认知障碍高风险。",
  "risk_level": "high",
  "recommended_tests": [
    "MMSE 或 MoCA",
    "头颅 MRI",
    "甲状腺功能",
    "维生素 B12 和叶酸",
    "ADL/IADL 量表"
  ],
  "disagreement_points": [],
  "next_steps": [
    "转诊认知障碍专科或神经内科",
    "完善可逆因素筛查",
    "建立随访和照护计划"
  ],
  "safety_notes": [
    "关注迷路和走失风险",
    "评估独立用药和厨房安全"
  ],
  "evidence_chunks": [
    "chunk_001.txt",
    "chunk_028.txt"
  ]
}
```

---

## 项目结构

```text
md_multiagents/
├── src/md_multiagents/
│   ├── main.py
│   ├── crew.py
│   ├── config/
│   │   ├── agents.yaml
│   │   └── tasks.yaml
│   └── tools/
│       ├── rag_tool.py
│       ├── generate_chunks.py
│       ├── risk_rules.py
│       ├── run_eval_cases.py
│       └── run_single_agent_eval.py
├── knowledge/
│   └── ad_chunks/
├── tests/
│   ├── ad_eval_cases.json
│   ├── eval_results.json
│   └── eval_summary.json
├── docs/
│   ├── project_summary.md
│   └── experiment_log.md
├── pyproject.toml
└── README.md
```

---

## 环境准备

推荐使用 Python 虚拟环境。

```bash
cd md_multiagents
python -m venv .venv
source .venv/bin/activate
```

如果使用 `uv`：

```bash
uv sync
```

或使用 pip 安装依赖：

```bash
pip install -e .
```

请在 `.env` 中配置模型 API，例如：

```env
MODEL=your-model-name
OPENAI_API_KEY=your-api-key
OPENAI_API_BASE=your-api-base
```

不同模型服务的变量名可能略有不同，请根据实际 LLM provider 调整。

---

## 运行主流程

运行交互式主流程：

```bash
crewai run
```

或直接运行入口：

```bash
python -m md_multiagents.main
```

输入一段中文病史后，系统会启动多智能体流程并输出最终结构化结果。

---

## 构建指南知识库 chunks

如果需要从指南文本重新生成 chunk：

```bash
python -m md_multiagents.tools.generate_chunks
```

生成结果默认保存到：

```text
knowledge/ad_chunks/
```

当前稳定版本使用关键词检索版 RAG。向量检索/FAISS 仍作为后续优化方向。

---

## 批量评测

运行全部测试病例：

```bash
python -m md_multiagents.tools.run_eval_cases \
  --cases-file tests/ad_eval_cases.json \
  --output tests/eval_results.json \
  --summary-output tests/eval_summary.json
```

运行单个病例：

```bash
python -m md_multiagents.tools.run_eval_cases \
  --cases-file tests/ad_eval_cases.json \
  --case-id AD-001 \
  --output tests/eval_AD001.json \
  --summary-output tests/eval_summary_AD001.json
```

重复运行某个病例，用于观察稳定性：

```bash
python -m md_multiagents.tools.run_eval_cases \
  --cases-file tests/ad_eval_cases.json \
  --case-id AD-001 \
  --repeat 3 \
  --output tests/eval_AD001_repeat.json
```

---

## Single-agent Baseline

运行单智能体 baseline：

```bash
python -m md_multiagents.tools.run_single_agent_eval \
  --cases-file tests/ad_eval_cases.json \
  --output tests/eval_results_single_agent.json \
  --summary-output tests/eval_summary_single_agent.json
```

该实验用于比较单一 Agent 与多智能体系统在同一测试集上的表现。

---

## Rule Checker

运行 rule checker demo：

```bash
python -m md_multiagents.tools.risk_rules --demo
```

评估一段自定义病史：

```bash
python -m md_multiagents.tools.risk_rules "患者近半年出现认知波动、反复视幻觉，并伴帕金森样动作迟缓。"
```

输出示例：

```json
{
  "rule_based_risk": "high",
  "matched_rules": [
    "DLB pattern: cognitive fluctuation + visual hallucination + parkinsonism"
  ]
}
```

Rule checker 不替代 LLM 决策，仅用于评测对照和高置信规则分析。

---

## 实验结果

当前实验主要包括：

| 测试设置                  |    病例数 |                          结果 |
| --------------------- | -----: | --------------------------: |
| Baseline cases        |      8 |                         8/8 |
| Extended cases        |     20 | Multi-agent accuracy ≈ 0.80 |
| Single-agent baseline |     20 |             Accuracy ≈ 0.65 |
| External public cases | 少量公开病例 |    qualitative sanity check |

说明：

* Baseline 和 extended cases 为人工构造的模拟病例，用于功能测试和边界分析。
* External public cases 来自公开病例报告或 clinical vignette 改写，仅用于定性 sanity check。
* 所有实验结果均不代表真实临床性能。

---

## 当前局限

* 测试集规模较小，且主要为 synthetic cases。
* 缺少医生标注和真实临床验证。
* RAG 当前为关键词检索，尚未稳定接入向量检索。
* 知识库主要基于 AD 指南，对 DLB、NPH、FTD 等扩展知识覆盖有限。
* 多智能体调用成本较高，运行时间长于单 Agent。
* LLM 输出仍存在一定非确定性。
* 本系统不能用于真实临床诊断或治疗决策。

---

## 后续工作

* 扩展认知障碍知识库，覆盖 DLB、NPH、FTD、VaD 和可逆性认知障碍。
* 引入向量检索，如 FAISS 或 Chroma。
* 引入更多公开病例和医生标注。
* 将 rule checker 与综合智能体进一步融合。
* 支持中间结果缓存，降低 API 成本。
* 增加前端界面和报告导出功能。

---

## 致谢

本项目参考了 CrewAI 框架、多智能体医学评估思想以及《中国阿尔茨海默病痴呆诊疗指南（2020）》中的相关诊疗建议。

---

## License

本项目仅用于课程学习和科研训练。若需公开发布，请根据项目成员约定补充开源协议。


