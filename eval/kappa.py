"""Cohen's κ（SPEC v0.2 §8.5）：label 分类 κ + pathology 多标签宏平均 κ。"""

PATHOLOGIES = [f"P{i}" for i in range(1, 12)]


def cohen_kappa(labels1, labels2):
    if len(labels1) != len(labels2):
        raise ValueError("两组标签长度须一致")
    n = len(labels1)
    if n == 0:
        return 0.0
    cats = sorted(set(labels1) | set(labels2))
    po = sum(1 for a, b in zip(labels1, labels2) if a == b) / n
    pe = sum((labels1.count(c) / n) * (labels2.count(c) / n) for c in cats)
    if pe >= 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def pathology_kappa(units1, units2):
    """按 uid 对齐的两组单元，对 P1–P11 逐项算二值 κ 再宏平均；双方均未出现的病症跳过。"""
    ks = []
    for p in PATHOLOGIES:
        l1 = [1 if p in u.get("pathology", []) else 0 for u in units1]
        l2 = [1 if p in u.get("pathology", []) else 0 for u in units2]
        if sum(l1) == 0 and sum(l2) == 0:
            continue
        ks.append(cohen_kappa(l1, l2))
    return sum(ks) / len(ks) if ks else 1.0
