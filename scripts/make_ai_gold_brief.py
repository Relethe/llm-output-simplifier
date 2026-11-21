"""提取非中文金标候选给外部标注 AI（T4.2 分流）：human/gold/non_chinese_gold.jsonl。
中文留给用户人工标（真人工校准）；非中文交外部 AI（AI 代理金标，报告区分，不冒充人工）。
运行：.venv\\Scripts\\python.exe -m scripts.make_ai_gold_brief
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_chinese(lang):
    return "chinese" in str(lang).lower()


def main():
    src = os.path.join(ROOT, "human", "gold", "gold_candidates.jsonl")
    with open(src, encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]
    non_zh = [it for it in items if not is_chinese(it.get("lang"))]
    zh = [it for it in items if is_chinese(it.get("lang"))]
    out = os.path.join(ROOT, "human", "gold", "non_chinese_gold.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for it in non_zh:
            slim = {"response_id": it["response_id"], "lang": it.get("lang"),
                    "category": it.get("category"), "question": it["question"],
                    "response": it["response"],
                    "units": [{"uid": u["uid"], "type": u["type"], "text": u["text"]} for u in it["units"]]}
            f.write(json.dumps(slim, ensure_ascii=False) + "\n")
    print("NON_CHINESE", len(non_zh), "-> non_chinese_gold.jsonl")
    print("CHINESE_FOR_USER", len(zh), [it["response_id"] for it in zh])
    print("DONE")


if __name__ == "__main__":
    main()
