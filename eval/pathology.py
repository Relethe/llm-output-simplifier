"""阶段 4 病理统计 + 理论上限（SPEC §8.6）。
pathology_stats：每病症句数占比 + 阅读时间占比 + 病症×类别×模型交叉。
theoretical_ceiling：删所有"删"、"压"压到 60%、move_first 前移后 T_总/T_答 降幅（所有方案天花板）。
"""
from eval.metrics import unit_length, speed_for, structure_switches, t_total, t_answer
from eval.aggregate import pct_reduction


def pathology_stats(annotations, speeds):
    total_units, total_time = 0, 0.0
    per_path, cross = {}, {}
    for a in annotations:
        for u in a["units"]:
            t = unit_length(u) / speed_for(u, speeds) * 60
            total_units += 1
            total_time += t
            for p in u.get("pathology", []):
                d = per_path.setdefault(p, {"count": 0, "time": 0.0})
                d["count"] += 1
                d["time"] += t
                key = (p, a["category"], a["model"])
                cross[key] = cross.get(key, 0) + 1
    stats = {p: {"count": d["count"],
                 "unit_frac": d["count"] / total_units if total_units else 0,
                 "time_frac": d["time"] / total_time if total_time else 0}
             for p, d in per_path.items()}
    return {"per_pathology": stats,
            "cross": {f"{p}|{c}|{m}": n for (p, c, m), n in cross.items()},
            "total_units": total_units}


def theoretical_ceiling(units, speeds, c, answer_uid):
    orig_tt = t_total(units, speeds, c)
    orig_ta = t_answer(units, speeds, c, answer_uid)
    kept = [u for u in units if u.get("label") != "删"]
    mf = [u for u in kept if u.get("move_first")]
    rest = [u for u in kept if not u.get("move_first")]
    ordered = mf + rest
    minutes = 0.0
    for u in ordered:
        L = unit_length(u)
        if u.get("label") == "压":
            L *= 0.6
        minutes += L / speed_for(u, speeds)
    ceil_tt = minutes * 60 + c * structure_switches(ordered)
    ceil_ta = t_answer(ordered, speeds, c, ordered[0]["uid"]) if ordered else 0.0
    return {"t_total_orig": orig_tt, "t_total_ceiling": ceil_tt,
            "t_total_red_pct": pct_reduction(orig_tt, ceil_tt),
            "t_answer_orig": orig_ta, "t_answer_ceiling": ceil_ta,
            "t_answer_red_pct": pct_reduction(orig_ta, ceil_ta)}
