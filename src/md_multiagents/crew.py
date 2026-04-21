from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class MdMultiagentsCrew():
    """多智能体医疗会诊团队"""

    # CrewAI 会自动从同级目录的 config 文件夹中读取那两个 YAML 文件
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # --- 注册 Agent ---
    @agent
    def nurse_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['nurse_agent'],
            verbose=True
        )

    @agent
    def doctor_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['doctor_agent'],
            verbose=True
        )

    # --- 注册 Task ---
    @task
    def extract_task(self) -> Task:
        return Task(
            config=self.tasks_config['extract_task'],
        )

    @task
    def diagnose_task(self) -> Task:
        return Task(
            config=self.tasks_config['diagnose_task'],
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
