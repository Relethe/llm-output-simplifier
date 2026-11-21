"""阶段 6 评测聚合（SPEC §10.2/10.3）：降幅、保留率、按类别×模型汇总 + bootstrap CI。"""
from eval.stats import bootstrap_ci


def pct_reduction(original, simplified):
    if original <= 0:
        return 0.0
    return (original - simplified) / original * 100


def retention_rate(held, total):
    if total <= 0:
        return 1.0  # 无必留点：平凡保留
    return held / total


def _group_stats(sub):
    n = len(sub)
    if n == 0:
        return {"n": 0}
    tt_red = [pct_reduction(x["t_total_orig"], x["t_total_simp"]) for x in sub]
    ta_red = [pct_reduction(x["t_answer_orig"], x["t_answer_simp"]) for x in sub]
    held = sum(x["held"] for x in sub)
    total = sum(x["total"] for x in sub)
    mean_tt, lo, hi = bootstrap_ci(tt_red)
    return {
        "n": n,
        "t_total_red_mean": mean_tt,
        "t_total_red_ci95": [lo, hi],
        "t_answer_red_mean": sum(ta_red) / n,
        "retention": retention_rate(held, total),
        "new_errors": sum(x["new_errors"] for x in sub),
        "blind_win_rate": sum(1 for x in sub if x["blind"] == "simplified") / n,
    }


def summarize(items):
    """items 每条含 category/model/t_total_orig/t_total_simp/t_answer_orig/t_answer_simp/
    held/total/new_errors/blind('simplified'/'original'/'tie')。返回 overall + by_category + by_model。"""
    return {
        "overall": _group_stats(items),
        "by_category": {c: _group_stats([x for x in items if x["category"] == c])
                        for c in sorted({x["category"] for x in items})},
        "by_model": {m: _group_stats([x for x in items if x["model"] == m])
                     for m in sorted({x["model"] for x in items})},
    }
