"""用真实评测数据填充用户亲手做材料（只备材料，不代做）。
- 盲评 30 对：原版 vs 简化，随机左右、去标签（make_blind_pairs）。
- 保留率复核 30：抽 30 个必留点，裁判判成立与否，供用户复核。
- 新增错误确认：重抽全部新增错误说法，供用户逐条确认。
运行：.venv\\Scripts\\python.exe -m scripts.prepare_eval_materials
"""
import os
import sys
import json
import random

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))
from scripts.llm_client import LLMClient, load_config  # noqa: E402
from scripts.prepare_human_data import make_blind_pairs  # noqa: E402
from eval.judges import retention_judge, new_errors_judge  # noqa: E402


def load_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def load_dir(d):
    return {json.load(open(os.path.join(d, f), encoding="utf-8"))["response_id"]:
            json.load(open(os.path.join(d, f), encoding="utf-8"))
            for f in os.listdir(d) if f.endswith(".json")}


def dump(path, items):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def main():
    client = LLMClient(load_config(os.path.join(ROOT, "config.yaml")), phase="dev")
    responses = {r["response_id"]: r for r in load_jsonl(os.path.join(ROOT, "responses", "responses_dev.jsonl"))}
    simpl = {r["response_id"]: r for r in load_jsonl(os.path.join(ROOT, "responses", "scheme_b_astra.jsonl"))}
    final = load_dir(os.path.join(ROOT, "annotations", "final"))
    rids = sorted(final)
    rng = random.Random(42)

    # 盲评 30 对
    pairs = [{"id": rid, "original": responses[rid]["response"], "simplified": simpl[rid]["simplified"]}
             for rid in rids if rid in simpl]
    blind = make_blind_pairs(pairs, n=30, seed=42)
    dump(os.path.join(ROOT, "human", "blind_eval", "blind_pairs.jsonl"), blind)

    # 保留率复核 30：抽 30 个必留点
    point_pool = [{"id": f"{rid}_p{p['pid']}", "point": p["text"], "simplified": simpl[rid]["simplified"]}
                  for rid in rids if rid in simpl for p in final[rid]["must_keep_points"]]
    checks = rng.sample(point_pool, min(30, len(point_pool)))
    for c in checks:
        c["judge_held"] = retention_judge(client, c["point"], c["simplified"])
    dump(os.path.join(ROOT, "human", "retention_check", "retention_checks.jsonl"), checks)

    # 新增错误：重抽全部说法
    errors = []
    for rid in rids:
        if rid not in simpl:
            continue
        for claim in new_errors_judge(client, responses[rid]["response"], simpl[rid]["simplified"]):
            errors.append({"response_id": rid, "claim": claim})
    dump(os.path.join(ROOT, "human", "retention_check", "new_errors.jsonl"), errors)

    print("BLIND_PAIRS", len(blind), "RETENTION_CHECKS", len(checks), "NEW_ERRORS", len(errors))
    print("spent", round(client.spent, 4))
    print("MATERIALS_DONE")


if __name__ == "__main__":
    main()
