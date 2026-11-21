"""阶段 7.1 代码测试（SPEC §11.1）自定义 runner。
SPEC-CHANGE-004：evalplus plus 沙箱在 Windows 挂死（reliability_guard 依赖 Unix resource）→
改用子进程跑 HumanEval **base** 测试（solution + check 断言 + 超时隔离），pass@1 不下降。
抽 50 题(seed42) × dev1 × original/A/B。数据/sanitize 仍用 evalplus 包。
运行：.venv\\Scripts\\python.exe -m scripts.run_code_test --n 50 --conditions original,A,B
"""
import os
import sys
import json
import random
import argparse
import subprocess

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
CACHE = os.path.join(ROOT, "data", "evalplus-cache")
os.makedirs(CACHE, exist_ok=True)
import evalplus.data.utils as _u  # noqa: E402
_u.CACHE_DIR = CACHE
import evalplus.data as _d  # noqa: E402
if hasattr(_d, "CACHE_DIR"):
    _d.CACHE_DIR = CACHE
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))
from evalplus.data import get_human_eval_plus  # noqa: E402
from evalplus.sanitize import sanitize  # noqa: E402
from scripts.llm_client import LLMClient, load_config  # noqa: E402
from scripts.evalplus_harness import extract_code  # noqa: E402
from schemes.scheme_a import build_messages  # noqa: E402
from schemes.scheme_b_rewrite import apply_scheme_B  # noqa: E402
from scripts.segment import segment  # noqa: E402


def gen_completion(client, problem, cond):
    prompt = problem["prompt"]
    if cond == "A":
        return client.call("dev1", build_messages(prompt, "A"), max_wall_s=240)["text"]
    text = client.call("dev1", [{"role": "user", "content": prompt}], max_wall_s=240)["text"]
    if cond == "B":
        return apply_scheme_B(client, segment(text))
    return text


def run_base_test(solution, problem, timeout=10):
    script = solution + "\n" + problem["test"] + "\ncheck(" + problem["entry_point"] + ")\n"
    try:
        proc = subprocess.run([sys.executable, "-c", script],
                              capture_output=True, text=True, timeout=timeout)
        return proc.returncode == 0
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--conditions", default="original,A,B")
    args = ap.parse_args()
    cfg = load_config(os.path.join(ROOT, "config.yaml"))
    client = LLMClient(cfg, phase="dev")
    problems = get_human_eval_plus()
    rng = random.Random(42)
    tids = rng.sample(sorted(problems), min(args.n, len(problems)))
    out_dir = os.path.join(ROOT, "eval", "evalplus")
    os.makedirs(out_dir, exist_ok=True)
    report = {}
    for cond in args.conditions.split(","):
        results = []
        for tid in tids:
            p = problems[tid]
            comp = gen_completion(client, p, cond)
            sol = sanitize(extract_code(comp or ""), p["entry_point"])
            results.append(run_base_test(sol, p))
        report[cond] = {"pass_at_1_base": sum(results) / len(results), "n": len(results)}
        print("COND", cond, "pass@1_base", report[cond]["pass_at_1_base"], flush=True)
    with open(os.path.join(out_dir, "code_test_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    orig = report.get("original", {}).get("pass_at_1_base")
    verdict = {c: (report[c]["pass_at_1_base"] >= orig if orig is not None else None) for c in report}
    print("PASS_AT_1_NOT_DROP", verdict, "spent", round(client.spent, 4))
    print("CODE_TEST_DONE")


if __name__ == "__main__":
    main()
