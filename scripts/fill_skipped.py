"""生成补缺：对 SKIP_EMPTY 缺失项用 effort=low 再试（SPEC-CHANGE-003 延伸）。
find_missing 纯函数可单测；main 在生成结束后跑，补齐缺失 response_id（仍空则记失败）。
运行：.venv\\Scripts\\python.exe -m scripts.fill_skipped
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
from scripts.generate_responses import build_entry, load_done, DEV_ROLES  # noqa: E402


def find_missing(prompts, roles, present_ids):
    expected = {f"{p['id']}_{r}" for p in prompts for r in roles}
    return sorted(expected - set(present_ids))


def main():
    cfg = load_config(os.path.join(ROOT, "config.yaml"))
    client = LLMClient(cfg, phase="dev")
    with open(os.path.join(ROOT, "data", "prompts_dev.jsonl"), encoding="utf-8") as f:
        prompts = [json.loads(line) for line in f if line.strip()]
    pmap = {p["id"]: p for p in prompts}
    out = os.path.join(ROOT, "responses", "responses_dev.jsonl")
    done = load_done(out)
    missing = find_missing(prompts, DEV_ROLES, done)
    print("MISSING", len(missing), missing)
    filled, still = 0, []
    with open(out, "a", encoding="utf-8") as f:
        for rid in missing:
            pid, role = rid.rsplit("_", 1)
            p = pmap[pid]
            msgs = [{"role": "user", "content": p["text"]}]
            try:
                res = client.call(role, msgs, max_wall_s=240, reasoning={"effort": "low"})
            except Exception:
                still.append(rid)
                continue
            if not (res["text"] or "").strip():
                still.append(rid)
                continue
            f.write(json.dumps(build_entry(p, role, res["meta"], res["text"]), ensure_ascii=False) + "\n")
            f.flush()
            filled += 1
    print("FILLED", filled, "STILL_EMPTY", still, "spent", round(client.spent, 4))
    print("FILL_DONE")


if __name__ == "__main__":
    main()
