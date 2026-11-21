"""汇总 Astra/Kimi 方案 B 批量简化结果，不调用模型。"""
import json
import os
from collections import Counter


def summarize_rows(rows):
    if not rows:
        return {"n": 0}
    reductions = [
        (r["original_chars"] - r["simplified_chars"]) / r["original_chars"] * 100
        for r in rows if r.get("original_chars", 0) > 0
    ]
    latencies = [r["simplifier_meta"]["latency_ms"] for r in rows]
    ops = Counter(op.get("op") for r in rows for op in r.get("ops", []))
    roles = Counter(r.get("simplifier_role") for r in rows)
    return {
        "n": len(rows),
        "mean_char_reduction_pct": sum(reductions) / len(reductions) if reductions else 0.0,
        "min_char_reduction_pct": min(reductions) if reductions else 0.0,
        "max_char_reduction_pct": max(reductions) if reductions else 0.0,
        "mean_latency_ms": sum(latencies) / len(latencies),
        "simplifier_roles": dict(roles),
        "ops": dict(ops),
    }


def main(path="responses/scheme_b_astra.jsonl", out="eval/scheme_b_astra_summary.json"):
    if not os.path.exists(path):
        print("NO_BATCH")
        return
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    report = {"overall": summarize_rows(rows)}
    for model in sorted({r["model"] for r in rows}):
        report["by_model_" + model] = summarize_rows([r for r in rows if r["model"] == model])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("SUMMARY_WRITTEN", out, "n", len(rows))


if __name__ == "__main__":
    main()
