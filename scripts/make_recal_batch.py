"""κ 重测新批（SPEC §8.5：改规范后换新批 15 条，不得同批反复调）。
选 15 条中文回答（不在原金标 30 内）→ G1 用保守口径标注 → 生成重测网页供用户标。
运行：.venv\\Scripts\\python.exe -m scripts.make_recal_batch
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
from scripts.segment import segment  # noqa: E402
from scripts.run_annotation import annotate_response  # noqa: E402
from scripts.make_gold_page import render_gold_page  # noqa: E402


def is_chinese(lang):
    return "chinese" in str(lang).lower()


def main():
    cfg = load_config(os.path.join(ROOT, "config.yaml"))
    client = LLMClient(cfg, phase="dev")
    with open(os.path.join(ROOT, "data", "prompts_dev.jsonl"), encoding="utf-8") as f:
        prompts = {json.loads(l)["id"]: json.loads(l) for l in f if l.strip()}
    with open(os.path.join(ROOT, "responses", "responses_dev.jsonl"), encoding="utf-8") as f:
        responses = [json.loads(l) for l in f if l.strip()]
    with open(os.path.join(ROOT, "human", "gold", "gold_candidates.jsonl"), encoding="utf-8") as f:
        orig_ids = {json.loads(l)["response_id"] for l in f if l.strip()}
    zh = [r for r in responses if is_chinese(prompts[r["prompt_id"]].get("lang")) and r["response_id"] not in orig_ids]
    rng = random.Random(42)
    batch = rng.sample(zh, min(15, len(zh)))
    items = []
    for r in batch:
        p = prompts[r["prompt_id"]]
        items.append({"response_id": r["response_id"], "question": p["text"], "response": r["response"],
                      "category": p["category"], "role": r["response_id"].rsplit("_", 1)[-1],
                      "lang": p.get("lang"), "units": segment(r["response"])})
    gold_dir = os.path.join(ROOT, "human", "gold")
    with open(os.path.join(gold_dir, "recal_candidates.jsonl"), "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    g1_dir = os.path.join(ROOT, "annotations", "g1_recal")
    os.makedirs(g1_dir, exist_ok=True)
    for it in items:
        obj, errs, meta = annotate_response(client, it["response_id"], it["question"], it["units"], "G1")
        json.dump(obj, open(os.path.join(g1_dir, it["response_id"] + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        if errs:
            print("G1_WARN", it["response_id"], errs)
    with open(os.path.join(gold_dir, "recal_annotation.html"), "w", encoding="utf-8") as f:
        f.write(render_gold_page(items))
    print("RECAL_BATCH", len(items), [it["response_id"] for it in items])
    print("spent", round(client.spent, 4))
    print("RECAL_BATCH_DONE")


if __name__ == "__main__":
    main()
