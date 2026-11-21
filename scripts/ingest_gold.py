"""接收用户金标导出（T4.2）：把 gold_user_annotations.json 数组拆成 human/gold/user/{rid}.json 单文件，
供 run_calibration 读取。校验 schema。运行：.venv\\Scripts\\python.exe -m scripts.ingest_gold
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from scripts.annotate import validate_annotation  # noqa: E402


def split_annotations(data):
    if isinstance(data, dict):
        data = [data]
    return {obj["response_id"]: obj for obj in data}


def main():
    user_dir = os.path.join(ROOT, "human", "gold", "user")
    src = os.path.join(user_dir, "gold_user_annotations.json")
    if not os.path.exists(src):
        print("NO_EXPORT（请把网页导出的 gold_user_annotations.json 放到 human/gold/user/）")
        return
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    objs = split_annotations(data)
    ok = 0
    for rid, obj in objs.items():
        errs = validate_annotation(obj)
        with open(os.path.join(user_dir, rid + ".json"), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        if not errs:
            ok += 1
        else:
            print("VALIDATE_WARN", rid, errs)
    print("INGESTED", len(objs), "valid", ok)
    print("INGEST_DONE")


if __name__ == "__main__":
    main()
