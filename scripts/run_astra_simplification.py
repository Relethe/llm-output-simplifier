"""Astra xhigh 方案 B 批量简化 runner。
逐条读取 responses_dev，流式/可续跑地生成 Astra edit ops，DeepSeek judge 校验 compress，
确定性重组后写 responses/scheme_b_astra.jsonl。记录原文/简化文本/ops/token/延迟/错误。
运行：.venv\\Scripts\\python.exe -m scripts.run_astra_simplification
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
from scripts.segment import segment  # noqa: E402
from schemes.scheme_b_rewrite import apply_scheme_B  # noqa: E402


def load_done(path):
    if not os.path.exists(path):
        return set()
    return {json.loads(line)["response_id"] for line in open(path, encoding="utf-8") if line.strip()}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="scheme_b_astra.jsonl", help="responses/ 下的输出文件名")
    args = ap.parse_args()
    cfg = load_config(os.path.join(ROOT, "config.yaml"))
    client = LLMClient(cfg, phase="dev")
    src = os.path.join(ROOT, "responses", "responses_dev.jsonl")
    out = os.path.join(ROOT, "responses", args.out)
    responses = [json.loads(line) for line in open(src, encoding="utf-8") if line.strip()]
    done = load_done(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    n, failed = 0, []
    with open(out, "a", encoding="utf-8") as f:
        for r in responses:
            rid = r["response_id"]
            if rid in done:
                continue
            try:
                units = segment(r["response"])
                used_role = "simplifier_external"
                try:
                    details = apply_scheme_B(client, units, return_details=True,
                                             simplifier_role=used_role)
                except Exception as primary_error:
                    # OpenExt Astra 超时/预算异常时切到用户指定的 Kimi 3.1 Pro
                    used_role = "simplifier_fallback"
                    details = apply_scheme_B(client, units, return_details=True,
                                             simplifier_role=used_role)
                    details["primary_error"] = type(primary_error).__name__ + ": " + str(primary_error)[:200]
                item = {"response_id": rid, "model": r["model"],
                        "simplifier_role": used_role,
                        "original": r["response"], "simplified": details["text"],
                        "ops": details["ops"], "sanitized_uids": details["sanitized_uids"],
                        "simplifier_meta": details["simplifier_meta"],
                        "original_units": len(units), "simplified_chars": len(details["text"]),
                        "original_chars": len(r["response"])}
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                f.flush()
                done.add(rid); n += 1
                if n % 10 == 0:
                    print("progress", n, "done", len(done), "spent", round(client.spent, 4), flush=True)
            except Exception as ex:
                failed.append({"response_id": rid, "error": type(ex).__name__ + ": " + str(ex)[:200]})
                print("SKIP", rid, failed[-1]["error"], flush=True)
    print("ASTRA_BATCH_DONE", "new", n, "total", len(done), "failed", len(failed), "spent", round(client.spent, 4))
    if failed:
        print("FAILED_IDS", [x["response_id"] for x in failed])


if __name__ == "__main__":
    main()
