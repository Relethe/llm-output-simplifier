"""人力材料数据填充（纯逻辑可单测）：为 6 步人力网页准备输入 jsonl。
- make_blind_pairs：原/简配对随机抽 30、随机左右、去标签（保留映射供计分）。
- find_disagreements：G1/G2 label 不一致单元 + 保守裁决。
- sample_retention_checks：裁判保留率判定随机抽 30。
- assign_timing_versions：40 条随机半原版/半简化（同一提问只读一版）。
main 在对应数据就绪后写 jsonl 并调用各网页生成器。
"""
import os
import sys
import json
import random

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from scripts.annotate import resolve_label  # noqa: E402


def make_blind_pairs(pairs, n=30, seed=42):
    rng = random.Random(seed)
    sel = rng.sample(pairs, min(n, len(pairs)))
    out = []
    for p in sel:
        if rng.random() < 0.5:
            a, b, simp_a = p["original"], p["simplified"], False
        else:
            a, b, simp_a = p["simplified"], p["original"], True
        out.append({"id": p["id"], "text_a": a, "text_b": b, "simplified_is_a": simp_a})
    return out


def find_disagreements(g1_units, g2_units):
    g2map = {u["uid"]: u for u in g2_units}
    out = []
    for u1 in g1_units:
        u2 = g2map.get(u1["uid"])
        if u2 and u1["label"] != u2["label"]:
            out.append({"uid": u1["uid"], "type": u1["type"], "text": u1["text"],
                        "g1_label": u1["label"], "g2_label": u2["label"],
                        "conservative": resolve_label(u1["label"], u2["label"])})
    return out


def sample_retention_checks(results, n=30, seed=42):
    rng = random.Random(seed)
    return rng.sample(results, min(n, len(results)))


def assign_timing_versions(items, seed=42):
    rng = random.Random(seed)
    idx = list(range(len(items)))
    rng.shuffle(idx)
    half = len(items) // 2
    out = []
    for k, i in enumerate(idx):
        it = items[i]
        ver = "original" if k < half else "simplified"
        out.append({"id": it["id"], "question": it["question"], "version": ver,
                    "text": it[ver], "quiz": it["quiz"]})
    return out


def _load(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _dump(path, items):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def main():
    # 各人力材料数据就绪后填充（缺数据则跳过）。网页生成器随后手动/自动跑。
    pairs = _load(os.path.join(ROOT, "eval", "blind_source_pairs.jsonl"))
    if pairs:
        _dump(os.path.join(ROOT, "human", "blind_eval", "blind_pairs.jsonl"), make_blind_pairs(pairs))
        print("BLIND_PAIRS_READY")
    checks = _load(os.path.join(ROOT, "eval", "retention_judge_results.jsonl"))
    if checks:
        _dump(os.path.join(ROOT, "human", "retention_check", "retention_checks.jsonl"),
              sample_retention_checks(checks))
        print("RETENTION_CHECKS_READY")
    timing = _load(os.path.join(ROOT, "eval", "timing_source.jsonl"))
    if timing:
        _dump(os.path.join(ROOT, "human", "timing", "timing_items.jsonl"), assign_timing_versions(timing))
        print("TIMING_ITEMS_READY")
    print("PREP_DONE（分歧清单待 G1/G2 标注后由 run_annotation 流程产出）")


if __name__ == "__main__":
    main()
