"""阶段 4 校准 + 放量编排（SPEC §8.5）。
校准：G1 金标 vs 用户金标 κ（label/pathology）≥0.6 放量；<0.6 改规范换新批 15 重测。
放量：G1/G2 独立标 200 → 必留点并集 → 分歧保守裁决(留>压>删) → annotations/final + 分歧清单(供 T4.5)。
compute_calibration/finalize_annotations 为纯函数（可单测）；main 待用户金标 + G1/G2 标注就绪后跑。
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from eval.kappa import cohen_kappa, pathology_kappa  # noqa: E402
from scripts.annotate import merge_must_keep, resolve_label  # noqa: E402


def compute_calibration(user_anns, g1_anns):
    labels_u, labels_g, units_u, units_g = [], [], [], []
    for rid, ua in user_anns.items():
        ga = g1_anns.get(rid)
        if not ga:
            continue
        gmap = {u["uid"]: u for u in ga["units"]}
        for uu in ua["units"]:
            gu = gmap.get(uu["uid"])
            if gu:
                labels_u.append(uu["label"])
                labels_g.append(gu["label"])
                units_u.append(uu)
                units_g.append(gu)
    return {"kappa_label": cohen_kappa(labels_u, labels_g),
            "kappa_pathology": pathology_kappa(units_u, units_g),
            "n_units": len(labels_u)}


def finalize_annotations(g1_anns, g2_anns):
    final, disagreements = {}, []
    for rid, a1 in g1_anns.items():
        a2 = g2_anns.get(rid)
        if not a2:
            continue
        points = merge_must_keep(a1["must_keep_points"], a2["must_keep_points"])
        g2map = {u["uid"]: u for u in a2["units"]}
        units = []
        for u1 in a1["units"]:
            u2 = g2map.get(u1["uid"], u1)
            label = resolve_label(u1["label"], u2["label"])
            if u1["label"] != u2["label"]:
                disagreements.append({"response_id": rid, "uid": u1["uid"], "type": u1["type"],
                                      "text": u1["text"], "g1_label": u1["label"],
                                      "g2_label": u2["label"], "conservative": label})
            units.append({**u1, "label": label})
        final[rid] = {**a1, "must_keep_points": points, "units": units, "annotator": "G1+G2"}
    return final, disagreements


def _load_dir(d):
    out = {}
    if not os.path.isdir(d):
        return out
    for fn in os.listdir(d):
        if fn.endswith(".json"):
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                obj = json.load(f)
            out[obj["response_id"]] = obj
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="SPEC-CHANGE-009：跳过 κ 关卡直接 finalize")
    args = ap.parse_args()
    user_gold = _load_dir(os.path.join(ROOT, "human", "gold", "user"))
    ai_gold = _load_dir(os.path.join(ROOT, "human", "gold", "ai"))
    g1_gold = _load_dir(os.path.join(ROOT, "annotations", "g1_gold"))
    if not g1_gold:
        print("NEED_G1_GOLD（须 G1 金标 annotations/g1_gold）")
        return
    human_cal = compute_calibration(user_gold, g1_gold) if user_gold else None
    ai_cal = compute_calibration(ai_gold, g1_gold) if ai_gold else None
    print("HUMAN_CALIBRATION_Chinese", json.dumps(human_cal, ensure_ascii=False))
    print("AI_AGREEMENT_nonChinese", json.dumps(ai_cal, ensure_ascii=False))
    gate = bool(human_cal and human_cal["kappa_label"] >= 0.6 and human_cal["kappa_pathology"] >= 0.6)
    print("GATE_human_kappa_ge_0.6", gate)
    g1 = _load_dir(os.path.join(ROOT, "annotations", "g1"))
    g2 = _load_dir(os.path.join(ROOT, "annotations", "g2"))
    if not g1 or not g2:
        print("FULL_ANNOTATION_PENDING（κ 达标后跑 run_annotation --mode full --variants G1,G2）")
        return
    if not gate and not args.force:
        print("KAPPA_BELOW_0.6（改规范 + 换新批 15 重测；--force 可按 SPEC-CHANGE-009 跳过）")
        return
    if args.force and not gate:
        print("SPEC-CHANGE-009：跳过 κ 关卡，AI 标注作工作标准（未经人工校准）")
    final, disagreements = finalize_annotations(g1, g2)
    fin_dir = os.path.join(ROOT, "annotations", "final")
    os.makedirs(fin_dir, exist_ok=True)
    for rid, obj in final.items():
        with open(os.path.join(fin_dir, rid + ".json"), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
    import random
    rng = random.Random(42)
    sample = rng.sample(disagreements, min(50, len(disagreements)))
    adj_dir = os.path.join(ROOT, "human", "adjudication")
    os.makedirs(adj_dir, exist_ok=True)
    with open(os.path.join(adj_dir, "disagreement_units.jsonl"), "w", encoding="utf-8") as f:
        for it in sample:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print("FINALIZED", len(final), "disagreements", len(disagreements), "sampled", len(sample))
    print("CALIBRATION_DONE")


if __name__ == "__main__":
    main()
