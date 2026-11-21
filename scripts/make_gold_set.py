"""阶段 4 金标集分层抽样（SPEC §8.5：30 条，四类×两模型覆盖）+ 备料。
stratified_gold 为纯函数（可单测）；main 在生成完成后运行，输出 human/gold/ 候选与单元。
运行：.venv\\Scripts\\python.exe -m scripts.make_gold_set
"""
import os
import sys
import json
import random

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from scripts.segment import segment  # noqa: E402

CATEGORIES = ["问答", "代码", "解释", "建议"]
ROLES = ["dev1", "dev2"]


def stratified_gold(items, n=30, seed=42):
    """按 (category, role) 分层抽 n 条，尽量均分、每层≥1，覆盖四类×两模型。"""
    rng = random.Random(seed)
    cells = {}
    for it in items:
        cells.setdefault((it["category"], it["role"]), []).append(it)
    keys = sorted(cells)
    for k in keys:
        rng.shuffle(cells[k])
    base, rem = n // len(keys), n % len(keys)
    sel = []
    for i, k in enumerate(keys):
        take = base + (1 if i < rem else 0)
        sel += cells[k][:take]
    return sel


def main():
    with open(os.path.join(ROOT, "data", "prompts_dev.jsonl"), encoding="utf-8") as f:
        prompts = {json.loads(line)["id"]: json.loads(line) for line in f if line.strip()}
    with open(os.path.join(ROOT, "responses", "responses_dev.jsonl"), encoding="utf-8") as f:
        responses = [json.loads(line) for line in f if line.strip()]
    items = []
    for r in responses:
        p = prompts.get(r["prompt_id"])
        if not p:
            continue
        role = r["response_id"].rsplit("_", 1)[-1]
        items.append({"response_id": r["response_id"], "prompt_id": r["prompt_id"],
                      "category": p["category"], "role": role, "lang": p["lang"],
                      "question": p["text"], "response": r["response"], "model": r["model"]})
    sel = stratified_gold(items, n=30, seed=42)
    out_dir = os.path.join(ROOT, "human", "gold")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "gold_candidates.jsonl"), "w", encoding="utf-8") as f:
        for it in sel:
            it["units"] = segment(it["response"])
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    from collections import Counter
    print("GOLD_N", len(sel))
    print("GOLD_CELLS", dict(Counter((x["category"], x["role"]) for x in sel)))
    print("GOLD_DONE")


if __name__ == "__main__":
    main()
