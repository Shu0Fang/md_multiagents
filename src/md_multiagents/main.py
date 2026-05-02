import sys
import json
from md_multiagents.crew import MdMultiagentsCrew


REQUIRED_FINAL_KEYS = [
    "final_judgment",
    "risk_level",
    "recommended_tests",
    "disagreement_points",
    "next_steps",
    "safety_notes",
    "evidence_chunks",
]


def _extract_json_payload(result):
    """Extract dict payload from CrewOutput when possible."""
    if isinstance(result, dict):
        return result

    json_dict = getattr(result, "json_dict", None)
    if isinstance(json_dict, dict) and json_dict:
        return json_dict

    raw = getattr(result, "raw", None)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return None

    return None


def _validate_final_payload(payload):
    """Validate required keys for synthesis output."""
    if not isinstance(payload, dict):
        print("[WARN] 最终输出不是 JSON object，跳过字段校验。")
        return

    missing = [k for k in REQUIRED_FINAL_KEYS if k not in payload]
    if missing:
        print(f"[WARN] 最终输出缺少字段: {', '.join(missing)}")
    else:
        print("[INFO] 最终输出字段校验通过。")

    evidence = payload.get("evidence_chunks")
    if not isinstance(evidence, list) or not evidence:
        print("[WARN] evidence_chunks 为空或格式不正确。")
        return

    invalid = [x for x in evidence if not isinstance(x, str) or not x.startswith("chunk_") or not x.endswith(".txt")]
    if invalid:
        print(f"[WARN] evidence_chunks 中存在非法条目: {invalid}")
    else:
        print("[INFO] evidence_chunks 格式校验通过。")


def _print_result(result):
    """Print Crew output safely: prefer structured JSON, then fall back to raw text."""
    payload = _extract_json_payload(result)
    if isinstance(payload, dict):
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    if isinstance(result, list):
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    json_dict = getattr(result, "json_dict", None)
    if isinstance(json_dict, dict) and json_dict:
        print(json.dumps(json_dict, indent=2, ensure_ascii=False))
        return

    raw = getattr(result, "raw", None)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            print(raw)
        return

    print(str(result))

def run():
    """
    运行你的医疗会诊团队
    """
    print(">>> 虚拟医疗团队已就绪。")
    
    # 模拟交互式输入
    patient_input = input("\n请在这里输入患者的纵向病历（按回车提交）: ")
    
    # 将输入组装成字典，对应 tasks.yaml 里的 {patient_record} 变量
    inputs = {
        'patient_record': patient_input
    }
    
    print("\n>>> 开始接诊患者，请稍候...\n")
    
    # 实例化上面的类，并启动 kickoff
    result = MdMultiagentsCrew().crew().kickoff(inputs=inputs)
    
    print("\n================ 最终会诊结果 ================\n")
    _print_result(result)

    # 对综合结果做最小字段校验，便于自动化链路稳定性检查
    _validate_final_payload(_extract_json_payload(result))


def train():
    """
    训练团队以给定的迭代次数。
    (用于自动化优化 Agent 的系统提示词)
    """
    inputs = {
        "patient_record": "患者男性，65岁。近半年来记忆力显著下降，在小区里找不到自己的家。脾气暴躁。无高血压糖尿病史。"
    }
    try:
        # sys.argv[1] 是你在终端输入的训练轮数，比如：crewai train 5
        MdMultiagentsCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)
        
    except Exception as e:
        raise Exception(f"训练团队时发生错误: {e}")


def replay():
    """
    从特定任务重新开始执行团队。
    (用于从错误或指定的 Task 节点重新开始执行)
    """
    try:
        # sys.argv[1] 是你在终端输入的 task_id，可以在上一次运行的日志中找到
        MdMultiagentsCrew().crew().replay(task_id=sys.argv[1])
        
    except Exception as e:
        raise Exception(f"重新播放团队时发生错误: {e}")


def test():
    """
    在测试集上批量评测医疗团队的准确率。
    """
    inputs = {
        "patient_record": "患者男性，65岁。近半年来记忆力显著下降，在小区里找不到自己的家。脾气暴躁。无高血压糖尿病史。"
    }
    try:
        # n_iterations 是你要测试的样本数量，openai_model_name 是用来当裁判评估结果的模型
        MdMultiagentsCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)
        
    except Exception as e:
        raise Exception(f"测试团队时发生错误: {e}")


if __name__ == "__main__":
    run()
