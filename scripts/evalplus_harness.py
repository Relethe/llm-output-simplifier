"""阶段 7.1 EvalPlus 代码测试核心（SPEC §11.1）：从回答提取代码 + pass@1。
extract_code/pass_at_1 为纯函数（可单测）；实际跑 EvalPlus 测试需 pip install evalplus，
用 evalplus.sanitize + evalplus.check_correctness 在子进程沙箱执行（不直接 exec 生成代码）。
运行：.venv\\Scripts\\python.exe -m scripts.evalplus_harness（生成各条件代码后跑测试）。
"""
import re


def extract_code(response):
    """提取 fenced python 代码块，取最长块为主解；无 fence 则退回原文。"""
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", response, re.DOTALL)
    if blocks:
        return max(blocks, key=len)
    return response


def pass_at_1(results):
    """results: 每题 bool（pass/fail）。pass@1 = 通过率。"""
    if not results:
        return 0.0
    return sum(1 for r in results if r) / len(results)


def main():
    # 部署 glue：抽 50 题（HumanEval+/MBPP+），各条件生成→extract_code→evalplus 沙箱测试→pass@1。
    # 需 evalplus 包；此处仅说明流程，实跑在阶段 7 接 EvalPlus 数据与 check_correctness。
    print("EvalPlus harness：需 pip install evalplus；抽 50 题各条件生成→extract_code→沙箱测试→pass@1 不下降")
    print("EVALPLUS_SKELETON")


if __name__ == "__main__":
    main()
