# MdMultiagents Crew

Welcome to the MdMultiagents Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/md_multiagents/config/agents.yaml` to define your agents
- Modify `src/md_multiagents/config/tasks.yaml` to define your tasks
- Modify `src/md_multiagents/crew.py` to add your own logic, tools and specific args
- Modify `src/md_multiagents/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the md_multiagents Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The md_multiagents Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

## Support

For support, questions, or feedback regarding the MdMultiagents Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.

## 阶段性成果

当前这个项目已经从最初的模板，推进到了一个用于 AD 风险评估的多智能体 MVP：

- 当前目标：AD 风险评估多智能体 MVP
- 当前流程：extraction -> 5 specialist agents -> synthesis
- 知识库：关键词 RAG，基于 ad_chunks
- 评测集：8 个模拟 case
- 当前结果：8/8 risk_level 通过

## 已知限制

虽然当前评测已经全部通过，但这个版本仍然有一些明确限制：

- 这是阶段性验证，不是医学真实世界验证
- 测试集规模很小，只有 8 个模拟 case
- 目前的 RAG 还是关键词检索，不是向量检索
- 模型输出仍然存在一定随机性，边界病例可能需要重复验证

后续如果要继续增强，可以再逐步补充更大规模的测试集、向量检索、结构化输出追踪以及更严格的回归评测。
