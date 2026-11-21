"""准备 T7.4 单人计时阅读材料（只备材料，不代做）。
抽 40 条：出题(必留点)→半原版/半简化分配→timing_items.jsonl→计时网页。
运行：.venv\\Scripts\\python.exe -m scripts.prepare_timing_material
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
from scripts.ai_reader_test import build_question_writer_messages  # noqa: E402
from scripts.run_ai_reader import parse_arr  # noqa: E402
from scripts.prepare_human_data import assign_timing_versions  # noqa: E402
from scripts.make_timing_page import render_timing_page  # noqa: E402


def load_dir(d):
    return {json.load(open(os.path.join(d, f), encoding="utf-8"))["response_id"]:
            json.load(open(os.path.join(d, f), encoding="utf-8"))
            for f in os.listdir(d) if f.endswith(".json")}


def main():
    client = LLMClient(load_config(os.path.join(ROOT, "config.yaml")), phase="dev")
    prompts = {json.loads(l)["id"]: json.loads(l)
               for l in open(os.path.join(ROOT, "data", "prompts_dev.jsonl"), encoding="utf-8") if l.strip()}
    responses = {json.loads(l)["response_id"]: json.loads(l)
                 for l in open(os.path.join(ROOT, "responses", "responses_dev.jsonl"), encoding="utf-8") if l.strip()}
    simpl = {json.loads(l)["response_id"]: json.loads(l)
             for l in open(os.path.join(ROOT, "responses", "scheme_b_astra.jsonl"), encoding="utf-8") if l.strip()}
    final = load_dir(os.path.join(ROOT, "annotations", "final"))
    rng = random.Random(42)
    rids = [r for r in rng.sample(sorted(final), min(40, len(final))) if r in simpl]
    items = []
    for rid in rids:
        points = final[rid]["must_keep_points"]
        quiz = []
        if points:
            qw = client.call("g1", build_question_writer_messages(points),
                             reasoning={"effort": "low"}, temperature=0, max_wall_s=120)
            quiz = parse_arr(qw["text"])[:3]
        pid = rid.rsplit("_", 1)[0]
        items.append({"id": rid, "question": prompts.get(pid, {}).get("text", ""),
                      "original": responses[rid]["response"], "simplified": simpl[rid]["simplified"],
                      "quiz": quiz})
    timing = assign_timing_versions(items, seed=42)
    out_dir = os.path.join(ROOT, "human", "timing")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "timing_items.jsonl"), "w", encoding="utf-8") as f:
        for it in timing:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    with open(os.path.join(out_dir, "timing_reading.html"), "w", encoding="utf-8") as f:
        f.write(render_timing_page(timing))
    print("TIMING_ITEMS", len(timing), "spent", round(client.spent, 4))
    print("TIMING_MATERIAL_DONE")


if __name__ == "__main__":
    main()
