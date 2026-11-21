"""阶段 4 标注运行器：G1/G2 独立会话标注（SPEC §8.5）。
GLM glm-5.3 带 reasoning.effort=medium + temperature=0 控开销保确定性。
--mode gold（金标 30，校准用）/ full（放量 200，须 κ≥0.6 校准通过后运行）。
逐条落盘 annotations/{g1,g2}/{response_id}.json，可续跑。
"""
import os
import sys
import json
import argparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))
from scripts.llm_client import LLMClient, load_config  # noqa: E402
from scripts.segment import segment  # noqa: E402
from scripts.annotation_prompts import build_annotation_messages, parse_annotation_json  # noqa: E402
from scripts.annotate import validate_annotation  # noqa: E402


def annotate_response(client, response_id, question, units, variant="G1", effort="low"):
    msgs = build_annotation_messages(response_id, question, units, variant)
    role = "g1" if variant == "G1" else "g2"
    res = client.call(role, msgs, reasoning={"effort": effort}, temperature=0)
    obj = parse_annotation_json(res["text"])
    # G1/G2 只输出最小 label（uid/label/move_first/pathology/note）；text/type 由切分合并补全
    lab_map = {u["uid"]: u for u in obj.get("units", [])}
    merged = []
    for su in units:
        lu = lab_map.get(su["uid"], {})
        merged.append({"uid": su["uid"], "type": su["type"], "text": su["text"],
                       "label": lu.get("label", "留"), "move_first": lu.get("move_first", False),
                       "pathology": lu.get("pathology", []), "note": lu.get("note", "")})
    obj["units"] = merged
    obj["response_id"] = response_id
    obj["annotator"] = variant
    errs = validate_annotation(obj)
    return obj, errs, res["meta"]


def load_items(mode):
    if mode == "gold":
        path = os.path.join(ROOT, "human", "gold", "gold_candidates.jsonl")
        with open(path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
    with open(os.path.join(ROOT, "data", "prompts_dev.jsonl"), encoding="utf-8") as f:
        prompts = {json.loads(line)["id"]: json.loads(line) for line in f if line.strip()}
    with open(os.path.join(ROOT, "responses", "responses_dev.jsonl"), encoding="utf-8") as f:
        responses = [json.loads(line) for line in f if line.strip()]
    items = []
    for r in responses:
        p = prompts.get(r["prompt_id"])
        if p:
            items.append({"response_id": r["response_id"], "question": p["text"],
                          "response": r["response"]})
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["gold", "full"], default="gold")
    ap.add_argument("--variants", default="G1,G2")
    args = ap.parse_args()
    cfg = load_config(os.path.join(ROOT, "config.yaml"))
    client = LLMClient(cfg, phase="dev")
    items = load_items(args.mode)
    variants = args.variants.split(",")
    n = 0
    for it in items:
        units = it.get("units") or segment(it["response"])
        for v in variants:
            sub = ("g1" if v == "G1" else "g2") + ("_gold" if args.mode == "gold" else "")
            out_dir = os.path.join(ROOT, "annotations", sub)
            os.makedirs(out_dir, exist_ok=True)
            out = os.path.join(out_dir, it["response_id"] + ".json")
            if os.path.exists(out):
                continue
            try:
                obj, errs, meta = annotate_response(client, it["response_id"], it["question"], units, v)
            except Exception:
                try:  # JSON 截断/解析失败 → low effort 重试（输出更短）
                    obj, errs, meta = annotate_response(client, it["response_id"], it["question"], units, v, effort="low")
                except Exception as ex:
                    print("ANNOT_SKIP", it["response_id"], v, type(ex).__name__, flush=True)
                    continue
            with open(out, "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
            n += 1
            if errs:
                print("VALIDATE_WARN", it["response_id"], v, errs, flush=True)
            if n % 20 == 0:
                print("progress", n, "spent", round(client.spent, 4), flush=True)
    print("ANNOTATED", n, "mode", args.mode, "spent", round(client.spent, 4))
    print("ANNOTATION_DONE")


if __name__ == "__main__":
    main()
