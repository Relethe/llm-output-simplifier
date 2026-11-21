"""给金标候选加中文翻译对照（T4.2 助读）：翻译 question+response 为简体中文。
标注仍针对原文单元（κ 有效），中文译文仅供阅读理解。运行：.venv\\Scripts\\python.exe -m scripts.translate_gold
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))
from scripts.llm_client import LLMClient, load_config  # noqa: E402

SYS = "把以下文本翻译成简体中文，保持原意与技术细节，只输出译文，不要解释。"


def translate(client, text):
    if not text:
        return ""
    try:
        res = client.call("g1", [{"role": "system", "content": SYS},
                                 {"role": "user", "content": text}],
                          reasoning={"effort": "low"}, temperature=0, max_wall_s=120)
        return (res["text"] or "").strip()
    except Exception:
        return ""


def main():
    client = LLMClient(load_config(os.path.join(ROOT, "config.yaml")), phase="dev")
    path = os.path.join(ROOT, "human", "gold", "gold_candidates.jsonl")
    with open(path, encoding="utf-8") as f:
        items = [json.loads(line) for line in f if line.strip()]
    for i, it in enumerate(items):
        if not it.get("zh_response"):
            it["zh_question"] = translate(client, it["question"])
            it["zh_response"] = translate(client, it["response"])
        if (i + 1) % 10 == 0:
            print("translated", i + 1, flush=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print("TRANSLATE_DONE", len(items))


if __name__ == "__main__":
    main()
