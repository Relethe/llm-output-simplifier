"""合并金标（T4.2 分流）：中文取用户人工标注，非中文取外部 AI 标注。
用户「human」文件中非中文为默认未动（全留），忽略；非中文以 AI 为准。
中文 → human/gold/user/{rid}.json（人工金标）；非中文 → human/gold/ai/{rid}.json（AI 代理金标）。
AI 单元仅 uid/label/...，从金标候选补全 type/text。运行：.venv\\Scripts\\python.exe -m scripts.merge_gold
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from scripts.annotate import validate_annotation  # noqa: E402

HUMAN_FILE = r"C:\Users\HUAWEI\Downloads\gold_user_annotations(human made).json"
AI_FILE = r"C:\Users\HUAWEI\Downloads\non_chinese_gold_annotations(AI made).json"


def is_chinese(lang):
    return "chinese" in str(lang).lower()


def load_map(path):
    d = json.load(open(path, encoding="utf-8"))
    return {x["response_id"]: x for x in (d if isinstance(d, list) else [d])}


def fill_units(ai_obj, cand_units):
    amap = {u["uid"]: u for u in ai_obj.get("units", [])}
    units = []
    for cu in cand_units:
        au = amap.get(cu["uid"], {})
        units.append({"uid": cu["uid"], "type": cu["type"], "text": cu["text"],
                      "label": au.get("label", "留"), "move_first": au.get("move_first", False),
                      "pathology": au.get("pathology", []), "note": au.get("note", "")})
    out = dict(ai_obj)
    out["units"] = units
    return out


def main():
    human = load_map(HUMAN_FILE)
    ai = load_map(AI_FILE)
    with open(os.path.join(ROOT, "human", "gold", "gold_candidates.jsonl"), encoding="utf-8") as f:
        cands = [json.loads(line) for line in f if line.strip()]
    user_dir = os.path.join(ROOT, "human", "gold", "user")
    ai_dir = os.path.join(ROOT, "human", "gold", "ai")
    os.makedirs(user_dir, exist_ok=True)
    os.makedirs(ai_dir, exist_ok=True)
    nu, na = 0, 0
    for c in cands:
        rid = c["response_id"]
        if is_chinese(c.get("lang")):
            if rid in human:
                obj = dict(human[rid]); obj["annotator"] = "user"
                errs = validate_annotation(obj)
                json.dump(obj, open(os.path.join(user_dir, rid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                nu += 1
                if errs:
                    print("USER_WARN", rid, errs)
        else:
            if rid in ai:
                obj = fill_units(ai[rid], c["units"]); obj["annotator"] = "AI"
                errs = validate_annotation(obj)
                json.dump(obj, open(os.path.join(ai_dir, rid + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                na += 1
                if errs:
                    print("AI_WARN", rid, errs)
    print("MERGED user(Chinese human)", nu, "ai(non-Chinese AI)", na)
    print("MERGE_DONE")


if __name__ == "__main__":
    main()
