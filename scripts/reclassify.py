"""T2.2 错分率 >10% 后重分类（SPEC §6）：用修订后的分类提示词重判现有 prompts_dev/test 的类别。
不重抽样（回答已生成），仅更新 category 元数据。运行：.venv\\Scripts\\python.exe -m scripts.reclassify
"""
import os
import sys
import json
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))
from scripts.llm_client import LLMClient, load_config  # noqa: E402
from scripts.sample_prompts import classify_prompt  # noqa: E402


def main():
    cfg = load_config(os.path.join(ROOT, "config.yaml"))
    client = LLMClient(cfg, phase="dev")
    for name in ["prompts_dev", "prompts_test"]:
        path = os.path.join(ROOT, "data", name + ".jsonl")
        with open(path, encoding="utf-8") as f:
            items = [json.loads(line) for line in f if line.strip()]
        changed = 0
        for it in items:
            old = it["category"]
            new = classify_prompt(client, it["text"])
            if new == "排除":
                new = old  # 已抽样 prompt 不因重判排除而丢失，保留原类
            if new != old:
                changed += 1
            it["category"] = new
        with open(path, "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        dist = dict(Counter(it["category"] for it in items))
        zh = dict(Counter(it["category"] for it in items if it.get("lang") == "Chinese" or "chinese" in str(it.get("lang", "")).lower()))
        print(name, "n", len(items), "changed", changed, "dist", dist, "zh", zh, flush=True)
    print("spent", round(client.spent, 4))
    print("RECLASSIFY_DONE")


if __name__ == "__main__":
    main()
