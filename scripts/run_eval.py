"""阶段 6 评测编排（SPEC §10）。对照 original/baseline/A/B/A+B + 消融。
须先有 annotations/final（must_keep_points + 单元 move_first）且校准通过。
逐条评测→按条件 summarize→eval/results.csv + eval_report.md。所有裁判结果属 AI 代理评测，待人工校准。
运行：.venv\\Scripts\\python.exe -m scripts.run_eval --conditions baseline,A,B,A+B
"""
import os
import sys
import json
import csv
import argparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))
from scripts.llm_client import LLMClient, load_config  # noqa: E402
from scripts.segment import segment  # noqa: E402
from schemes.scheme_a import build_messages  # noqa: E402
from schemes.scheme_b_rewrite import apply_scheme_B  # noqa: E402
from eval.metrics import t_total, t_answer  # noqa: E402
from eval.judges import retention_judge, new_errors_judge, blind_eval  # noqa: E402
from eval.aggregate import summarize  # noqa: E402


def get_answer_uid(ann_units):
    """直接回答单元：取首个 move_first=true 的 uid；若无（答案在开头）则 uid=1。"""
    for u in ann_units:
        if u.get("move_first"):
            return u["uid"]
    return 1


def regen(client, role, question, mode, remove=None):
    res = client.call(role, build_messages(question, mode, remove))
    return res["text"]


def condition_text(client, item, cond, orig_units):
    if cond == "original":
        return item["response"]
    if cond == "baseline":
        return regen(client, item["role"], item["question"], "baseline")
    if cond == "A":
        return regen(client, item["role"], item["question"], "A")
    if cond == "B":
        return apply_scheme_B(client, orig_units)
    if cond == "A+B":
        return apply_scheme_B(client, segment(regen(client, item["role"], item["question"], "A")))
    if cond.startswith("A_no"):
        return regen(client, item["role"], item["question"], "A", remove=int(cond[4:]))
    raise ValueError(f"unknown condition {cond}")


def evaluate_one(client, item, speeds, c, cond):
    orig = item["response"]
    orig_units = segment(orig)
    ann = item["annotation"]
    points = ann["must_keep_points"]
    answer_uid = get_answer_uid(ann["units"])
    text = condition_text(client, item, cond, orig_units)
    su = segment(text)
    bl = blind_eval(client, orig, text)
    blmap = {"A": "original", "B": "simplified", "一样": "tie"}
    return {
        "category": item["category"], "model": item["model"],
        "t_total_orig": t_total(orig_units, speeds, c), "t_total_simp": t_total(su, speeds, c),
        "t_answer_orig": t_answer(orig_units, speeds, c, answer_uid),
        "t_answer_simp": t_answer(su, speeds, c, answer_uid),
        "held": sum(1 for p in points if retention_judge(client, p["text"], text)),
        "total": len(points), "new_errors": len(new_errors_judge(client, orig, text)),
        "blind": blmap[bl],
    }


def load_eval_items():
    with open(os.path.join(ROOT, "data", "prompts_dev.jsonl"), encoding="utf-8") as f:
        prompts = {json.loads(line)["id"]: json.loads(line) for line in f if line.strip()}
    with open(os.path.join(ROOT, "responses", "responses_dev.jsonl"), encoding="utf-8") as f:
        responses = [json.loads(line) for line in f if line.strip()]
    items = []
    for r in responses:
        ann_path = os.path.join(ROOT, "annotations", "final", r["response_id"] + ".json")
        if not os.path.exists(ann_path):
            continue
        with open(ann_path, encoding="utf-8") as f:
            ann = json.load(f)
        p = prompts[r["prompt_id"]]
        items.append({"response_id": r["response_id"], "prompt_id": r["prompt_id"],
                      "role": r["response_id"].rsplit("_", 1)[-1], "question": p["text"],
                      "response": r["response"], "category": p["category"],
                      "model": r["model"], "annotation": ann})
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conditions", default="baseline,A,B,A+B")
    args = ap.parse_args()
    cfg = load_config(os.path.join(ROOT, "config.yaml"))
    client = LLMClient(cfg, phase="dev")
    with open(os.path.join(ROOT, "reading_speed.json"), encoding="utf-8") as f:
        speeds = json.load(f)
    c = speeds["c_structure_switch"]["value"]
    items = load_eval_items()
    if not items:
        print("NO_FINAL_ANNOTATIONS（须先完成阶段4标注+校准）")
        return
    conditions = [x for x in args.conditions.split(",") if x != "original"]
    rows = []
    for it in items:
        for cond in conditions:
            r = evaluate_one(client, it, speeds, c, cond)
            r["condition"] = cond
            r["response_id"] = it["response_id"]
            rows.append(r)
    os.makedirs(os.path.join(ROOT, "eval"), exist_ok=True)
    with open(os.path.join(ROOT, "eval", "results.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    report = {cond: summarize([r for r in rows if r["condition"] == cond]) for cond in conditions}
    with open(os.path.join(ROOT, "eval", "eval_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("EVAL_ITEMS", len(items), "conditions", conditions, "spent", round(client.spent, 4))
    print("EVAL_DONE")


if __name__ == "__main__":
    main()
