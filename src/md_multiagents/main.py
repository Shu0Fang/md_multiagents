import sys
from md_multiagents.crew import MdMultiagentsCrew

def run():
    """
    运行你的医疗会诊团队
    """
    print(">>> 虚拟医疗团队已就绪。")
    
    # 模拟交互式输入
    patient_input = input("\n请在这里输入患者的真实主诉（按回车提交）: ")
    
    # 将输入组装成字典，对应 tasks.yaml 里的 {patient_case} 变量
    inputs = {
        'patient_case': patient_input
    }
    
    print("\n>>> 开始接诊患者，请稍候...\n")
    
    # 实例化上面的类，并启动 kickoff
    result = MdMultiagentsCrew().crew().kickoff(inputs=inputs)
    
    print("\n================ 最终会诊结果 ================\n")
    print(result)


def train():
    """
    Train the crew for a given number of iterations.
    (用于自动化优化 Agent 的系统提示词)
    """
    inputs = {
        "patient_case": "患者男性，65岁。近半年来记忆力显著下降，在小区里找不到自己的家。脾气暴躁。无高血压糖尿病史。"
    }
    try:
        # sys.argv[1] 是你在终端输入的训练轮数，比如：crewai train 5
        MdMultiagentsCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)
        
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    (用于从报错或指定的 Task 节点重新开始执行)
    """
    try:
        # sys.argv[1] 是你在终端输入的 task_id，可以在上一次运行的日志中找到
        MdMultiagentsCrew().crew().replay(task_id=sys.argv[1])
        
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    (用于在测试集上批量评测医疗团队的准确率)
    """
    inputs = {
        "patient_case": "患者男性，65岁。近半年来记忆力显著下降，在小区里找不到自己的家。脾气暴躁。无高血压糖尿病史。"
    }
    try:
        # n_iterations 是你要测试的样本数量，openai_model_name 是用来当裁判评估结果的模型
        MdMultiagentsCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)
        
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

if __name__ == "__main__":
    run()
