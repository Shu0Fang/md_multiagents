import os

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
from md_multiagents.tools.rag_tool import RagTool

@CrewBase
class MdMultiagentsCrew():
    """多智能体医疗会诊团队"""

    # CrewAI 会自动从同级目录的 config 文件夹中读取那两个 YAML 文件
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def _build_llm(self) -> LLM:
        model_name = os.getenv("MODEL") or os.getenv("OPENAI_MODEL_NAME") or "deepseek-chat"
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE") or os.getenv("OPENAI_BASE_URL")

        return LLM(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=0,
        )

    # --- 注册 Agent ---
    @agent
    def data_extraction_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['data_extraction_agent'],
            llm=self._build_llm(),
            verbose=True
        )

    @agent
    def primary_care_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['primary_care_agent'],
            llm=self._build_llm(),
            tools=[RagTool()],
            verbose=True
        )

    @agent
    def neurologist_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['neurologist_agent'],
            llm=self._build_llm(),
            tools=[RagTool()],
            verbose=True
        )

    @agent
    def geriatrician_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['geriatrician_agent'],
            llm=self._build_llm(),
            tools=[RagTool()],
            verbose=True
        )

    @agent
    def psychiatrist_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['psychiatrist_agent'],
            llm=self._build_llm(),
            tools=[RagTool()],
            verbose=True
        )

    @agent
    def psychologist_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['psychologist_agent'],
            llm=self._build_llm(),
            tools=[RagTool()],
            verbose=True
        )

    @agent
    def ad_specialist_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['ad_specialist_agent'],
            llm=self._build_llm(),
            tools=[RagTool()],
            verbose=True
        )

    # --- 注册 Task ---
    @task
    def extraction_task(self) -> Task:
        return Task(
            config=self.tasks_config['extraction_task'],
        )

    @task
    def primary_care_task(self) -> Task:
        return Task(
            config=self.tasks_config['primary_care_task'],
        )

    @task
    def neurologist_task(self) -> Task:
        return Task(
            config=self.tasks_config['neurologist_task'],
        )

    @task
    def geriatrician_task(self) -> Task:
        return Task(
            config=self.tasks_config['geriatrician_task'],
        )

    @task
    def psychiatrist_task(self) -> Task:
        return Task(
            config=self.tasks_config['psychiatrist_task'],
        )

    @task
    def psychologist_task(self) -> Task:
        return Task(
            config=self.tasks_config['psychologist_task'],
        )

    @task
    def synthesis_task(self) -> Task:
        return Task(
            config=self.tasks_config['synthesis_task'],
        )

    # --- 组装 Crew ---
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents, # 自动获取上面 @agent 装饰的函数
            tasks=self.tasks,   # 自动获取上面 @task 装饰的函数
            process=Process.sequential,
            verbose=True,
        )
