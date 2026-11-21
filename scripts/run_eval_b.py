"""阶段 6 评测（复用预计算方案 B 简化结果，不重复调简化器）。
T_总/T_答 降幅为纯计算；--judge 时追加保留率/新增错误/盲评（DeepSeek 裁判，AI 代理）。
按 4 类别 × 2 模型汇总。运行：.venv\\Scripts\\python.exe -m scripts.run_eval_b [--judge]
"""
import os
import sys
import json
import argparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from scripts.segment import segment  # noqa: E402
from eval.metrics import t_total, t_answer  # noqa: E402
from eval.aggregate import summarize  # noqa: E402
from scripts.run_eval import get_answer_uid  # noqa: E402
from eval.judges import retention_judge, new_errors_judge, blind_eval  # noqa: E402
from scripts.llm_client import LLMClient, load_config  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))


def load_jsonl_map(path, key="response_id"):
    return {json.loads(l)[key]: json.loads(l) for l in open(path, encoding="utf-8") if l.strip()}


def load_dir_map(d):
    out = {}
    for fn in os.listdir(d):
        if fn.endswith(".json"):
            o = json.load(open(os.path.join(d, fn), encoding="utf-8"))
            out[o["response_id"]] = o
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", action="store_true", help="追加保留率/新增错误/盲评裁判")
    ap.add_argument("--simpl", default="scheme_b_astra.jsonl", help="responses/ 下的简化结果文件")
    ap.add_argument("--out", default=None, help="eval/ 下输出 json 名（默认按 judge 自动）")
    args = ap.parse_args()
    speeds = json.load(open(os.path.join(ROOT, "reading_speed.json"), encoding="utf-8"))
    c = speeds["c_structure_switch"]["value"]
    prompts = load_jsonl_map(os.path.join(ROOT, "data", "prompts_dev.jsonl"), key="id")
    responses = load_jsonl_map(os.path.join(ROOT, "responses", "responses_dev.jsonl"))
    simpl = load_jsonl_map(os.path.join(ROOT, "responses", args.simpl))
    final = load_dir_map(os.path.join(ROOT, "annotations", "final"))

    items = []
    for rid, fin in final.items():
        if rid not in responses or rid not in simpl:
            continue
        pid = rid.rsplit("_", 1)[0]
        cat = prompts.get(pid, {}).get("category", "?")
        model = responses[rid]["model"]
        ou = segment(responses[rid]["response"])
        su = segment(simpl[rid]["simplified"])
        answer_uid = get_answer_uid(fin["units"])
        items.append({
            "response_id": rid, "category": cat, "model": model,
            "t_total_orig": t_total(ou, speeds, c), "t_total_simp": t_total(su, speeds, c),
            "t_answer_orig": t_answer(ou, speeds, c, answer_uid),
            "t_answer_simp": t_answer(su, speeds, c, answer_uid),
            "held": 0, "total": len(fin["must_keep_points"]), "new_errors": 0, "blind": "tie",
        })

    if args.judge:
        client = LLMClient(load_config(os.path.join(ROOT, "config.yaml")), phase="dev")
        ckpt_path = os.path.join(ROOT, "eval", (args.out or "eval_b_full.json") + ".ckpt.jsonl")
        done = {}
        if os.path.exists(ckpt_path):
            for l in open(ckpt_path, encoding="utf-8"):
                if l.strip():
                    o = json.loads(l)
                    done[o["response_id"]] = o
        ckpt = open(ckpt_path, "a", encoding="utf-8")
        n_judged = 0
        for i, it in enumerate(items):
            rid = it["response_id"]
            if rid in done:
                it.update(done[rid])
                continue
            simp_text = simpl[rid]["simplified"]
            orig_text = responses[rid]["response"]
            points = final[rid]["must_keep_points"]
            ok = False
            for attempt in range(2):
                try:
                    it["held"] = sum(1 for p in points if retention_judge(client, p["text"], simp_text))
                    it["new_errors"] = len(new_errors_judge(client, orig_text, simp_text))
                    bl = blind_eval(client, orig_text, simp_text)
                    it["blind"] = {"A": "original", "B": "simplified", "一样": "tie"}[bl]
                    ok = True
                    break
                except Exception as ex:
                    print("JUDGE_RETRY", rid, type(ex).__name__, flush=True)
            if not ok:
                it["judge_error"] = True
                print("JUDGE_SKIP", rid, flush=True)
            ckpt.write(json.dumps(it, ensure_ascii=False) + "\n")
            ckpt.flush()
            n_judged += 1
            if n_judged % 20 == 0:
                print("judge progress", n_judged, "spent", round(client.spent, 4), flush=True)
        ckpt.close()
    n_err = sum(1 for it in items if it.get("judge_error"))
    items = [it for it in items if not it.get("judge_error")]
    report = summarize(items)
    default_out = "eval_b_full.json" if args.judge else "eval_b_metrics.json"
    out = os.path.join(ROOT, "eval", args.out or default_out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"n": len(items), "judge_error_excluded": n_err,
                   "note": "T_总/T_答 为实测计算；保留率/盲评为 AI 代理裁判·未经人工校准；中文速度占位·推断",
                   "summary": report}, f, ensure_ascii=False, indent=2)
    ov = report["overall"]
    print("EVAL_B_METRICS n", len(items), "judge_error_excluded", n_err)
    print("T_total_red_mean", round(ov["t_total_red_mean"], 2), "CI95", [round(x, 2) for x in ov["t_total_red_ci95"]])
    print("T_answer_red_mean", round(ov["t_answer_red_mean"], 2))
    for m, s in report["by_model"].items():
        print("model", m, "T_total_red", round(s["t_total_red_mean"], 2), "T_answer_red", round(s["t_answer_red_mean"], 2))
    print("EVAL_B_METRICS_DONE")


if __name__ == "__main__":
    main()
