"""阶段 7.1 EvalPlus 代码测试运行器（SPEC §11.1，全自动）。
抽 50 题 HumanEval+，dev1 在 original/A/B 条件下生成→extract_code+sanitize→evalplus 沙箱测试→pass@1。
通过标准：各方案 pass@1 不下降（相对 original）。CACHE_DIR 补丁到项目内（AppData 拒绝访问）。
运行：.venv\\Scripts\\python.exe -m scripts.run_evalplus --n 50 --conditions original,A,B
"""
import os
import sys
import json
import glob
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
        res = client.call("dev1", build_messages(prompt, "A"), max_wall_s=240)
        return res["text"]
    res = client.call("dev1", [{"role": "user", "content": prompt}], max_wall_s=240)
    if cond == "B":
        return apply_scheme_B(client, segment(res["text"]))
    return res["text"]


def read_pass_at_1(samples_path, tid_set=None):
    cand = glob.glob(samples_path + "*eval_results*.jsonl") + glob.glob(samples_path.replace(".jsonl", "") + "*results*.jsonl")
    if not cand:
        return None, None
    rows = [json.loads(l) for l in open(cand[0], encoding="utf-8") if l.strip()]
    if tid_set is not None:
        rows = [r for r in rows if r.get("task_id") in tid_set]  # 只统计抽样题
    plus = [r.get("plus_status") == "pass" for r in rows]
    base = [r.get("base_status") == "pass" for r in rows]
    p1 = sum(plus) / len(plus) if plus else None
    b1 = sum(base) / len(base) if base else None
    return p1, b1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--conditions", default="original,A,B")
    args = ap.parse_args()
    cfg = load_config(os.path.join(ROOT, "config.yaml"))
    client = LLMClient(cfg, phase="dev")
    problems = get_human_eval_plus()
    rng = random.Random(42)
    all_tids = sorted(problems)
    tids = rng.sample(all_tids, min(args.n, len(all_tids)))
    tid_set = set(tids)
    out_dir = os.path.join(ROOT, "eval", "evalplus")
    os.makedirs(out_dir, exist_ok=True)
    report = {}
    for cond in args.conditions.split(","):
        samples = []
        for tid in all_tids:  # CLI 要求覆盖全 164 题；非抽样题占位，pass@1 只算抽样 50
            p = problems[tid]
            if tid in tid_set:
                comp = gen_completion(client, p, cond)
                code = sanitize(extract_code(comp or ""), p["entry_point"])
            else:
                code = "pass"
            samples.append({"task_id": tid, "completion": code})
        sf = os.path.join(out_dir, f"samples_{cond}.jsonl")
        with open(sf, "w", encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        wrapper = os.path.join(ROOT, "scripts", "_evalplus_run.py")
        proc = subprocess.run([sys.executable, wrapper, "humaneval", "--samples", sf, "--parallel", "1"],
                              capture_output=True, text=True, timeout=1800)
        p1, b1 = read_pass_at_1(sf, tid_set)
        report[cond] = {"pass_at_1_plus": p1, "pass_at_1_base": b1, "n": len(tids)}
        print("COND", cond, "pass@1_plus", p1, "base", b1, flush=True)
        if proc.returncode != 0:
            print("EVALCLI_WARN", cond, proc.stderr[-300:], flush=True)
    with open(os.path.join(out_dir, "evalplus_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    orig = report.get("original", {}).get("pass_at_1_plus")
    verdict = {c: (report[c]["pass_at_1_plus"] >= orig if orig is not None and report[c]["pass_at_1_plus"] is not None else None)
               for c in report}
    print("PASS_AT_1_NOT_DROP", verdict)
    print("spent", round(client.spent, 4))
    print("EVALPLUS_DONE")


if __name__ == "__main__":
    main()
