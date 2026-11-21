"""阶段 3 生成原始回答（SPEC v0.2 §7）：dev 100 提问 × 2 开发模型 = 200 条。
不加系统提示词、各模型默认参数、每条生成 1 次。逐条 append+flush（崩溃可续跑）。
字段：response_id, prompt_id, model, model_version, params, response, tokens_out, latency_ms, timestamp。
运行：.venv\\Scripts\\python.exe -m scripts.generate_responses
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))
from scripts.llm_client import LLMClient, load_config  # noqa: E402

DEV_ROLES = ["dev1", "dev2"]


def build_entry(prompt, role, meta, text):
    return {
        "response_id": f"{prompt['id']}_{role}",
        "prompt_id": prompt["id"],
        "model": meta["model"],
        "model_version": meta["model_version"],
        "params": meta["params"],
        "response": text,
        "tokens_out": meta["tokens_out"],
        "latency_ms": meta["latency_ms"],
        "timestamp": meta["timestamp"],
    }


def load_done(path):
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {json.loads(line)["response_id"] for line in f if line.strip()}


def main():
    cfg = load_config(os.path.join(ROOT, "config.yaml"))
    client = LLMClient(cfg, phase="dev")
    with open(os.path.join(ROOT, "data", "prompts_dev.jsonl"), encoding="utf-8") as f:
        prompts = [json.loads(line) for line in f if line.strip()]
    out_dir = os.path.join(ROOT, "responses")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "responses_dev.jsonl")
    done = load_done(out)
    n = 0
    failures = []
    with open(out, "a", encoding="utf-8") as f:
        for p in prompts:
            for role in DEV_ROLES:
                rid = f"{p['id']}_{role}"
                if rid in done:
                    continue
                # SPEC §7：无系统提示、默认参数；墙钟上限 240s 防默认推理无休止（SPEC-CHANGE-003）
                msgs = [{"role": "user", "content": p["text"]}]
                try:
                    # SPEC-CHANGE-005/006：dev1(GLM)/dev2(Qwen)均推理模型，默认推理慢→直接 effort=low（输出仍自然）
                    res = client.call(role, msgs, max_wall_s=120, reasoning={"effort": "low"})
                except Exception as ex:
                    failures.append(rid)
                    print("SKIP_ERROR", rid, type(ex).__name__, flush=True)
                    continue
                if not (res["text"] or "").strip():
                    failures.append(rid)
                    print("SKIP_EMPTY", rid, flush=True)
                    continue
                e = build_entry(p, role, res["meta"], res["text"])
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
                f.flush()
                done.add(rid)
                n += 1
                if n % 20 == 0:
                    print("progress", n, "spent", round(client.spent, 4), flush=True)
    print("GENERATED", n, "total_done", len(done), "failures", failures, "spent", round(client.spent, 4))
    print("GENERATION_DONE")


if __name__ == "__main__":
    main()
