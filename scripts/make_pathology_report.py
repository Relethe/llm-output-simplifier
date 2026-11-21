"""阶段 4 病理报告生成（SPEC §8.6）：读 annotations/final → reports/pathology_report.md。
病理×类别×模型交叉 + 句数/时间占比 + P8 出现率 + T_答 分布 + 理论上限（所有方案天花板）。
须先有 annotations/final（校准放量后）。运行：.venv\\Scripts\\python.exe -m scripts.make_pathology_report
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from eval.pathology import pathology_stats, theoretical_ceiling  # noqa: E402
from eval.metrics import t_answer  # noqa: E402
from scripts.run_eval import get_answer_uid  # noqa: E402


def main():
    fin_dir = os.path.join(ROOT, "annotations", "final")
    if not os.path.isdir(fin_dir) or not os.listdir(fin_dir):
        print("NEED_FINAL_ANNOTATIONS（须先校准放量）")
        return
    with open(os.path.join(ROOT, "data", "prompts_dev.jsonl"), encoding="utf-8") as f:
        prompts = {json.loads(l)["id"]: json.loads(l) for l in f if l.strip()}
    with open(os.path.join(ROOT, "reading_speed.json"), encoding="utf-8") as f:
        speeds = json.load(f)
    c = speeds["c_structure_switch"]["value"]
    anns, ceilings, t_answers = [], [], []
    p8 = 0
    for fn in os.listdir(fin_dir):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(fin_dir, fn), encoding="utf-8") as f:
            a = json.load(f)
        rid = a["response_id"]
        pid = rid.rsplit("_", 1)[0]
        role = rid.rsplit("_", 1)[-1]
        cat = prompts.get(pid, {}).get("category", "?")
        units = a["units"]
        anns.append({"category": cat, "model": role, "units": units})
        answer_uid = get_answer_uid(units)
        ceilings.append(theoretical_ceiling(units, speeds, c, answer_uid))
        t_answers.append(t_answer(units, speeds, c, answer_uid))
        if any("P8" in u.get("pathology", []) for u in units):
            p8 += 1
    stats = pathology_stats(anns, speeds)
    n = len(anns)
    avg_red = sum(x["t_total_red_pct"] for x in ceilings) / n if n else 0
    avg_ta_red = sum(x["t_answer_red_pct"] for x in ceilings) / n if n else 0
    out = os.path.join(ROOT, "reports", "pathology_report.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("# 病理统计报告（SPEC §8.6）\n\n")
        f.write(f"> 证据类型：AI 代理评测（G1/G2 标注，经用户金标 κ 校准）。回答数 {n}。\n\n")
        f.write("## 病症占比（句数 / 阅读时间）\n\n| 病症 | 句数 | 句数占比 | 时间占比 |\n|---|---|---|---|\n")
        for p in sorted(stats["per_pathology"]):
            d = stats["per_pathology"][p]
            f.write(f"| {p} | {d['count']} | {d['unit_frac']:.3f} | {d['time_frac']:.3f} |\n")
        f.write("\n## 病症 × 类别 × 模型交叉\n\n| 病症|类别|模型 | 句数 |\n|---|---|\n")
        for k in sorted(stats["cross"]):
            f.write(f"| {k} | {stats['cross'][k]} |\n")
        f.write(f"\n## P8 答案后置\n\n出现率：{p8}/{n} = {p8/n:.3f}\n")
        f.write(f"\n## T_答 分布（秒）\n\nmin={min(t_answers):.1f} max={max(t_answers):.1f} mean={sum(t_answers)/n:.1f}\n")
        f.write(f"\n## 理论上限（所有方案天花板）\n\n删所有「删」、压到 60%、move_first 前移后：\n")
        f.write(f"- T_总 平均降幅：**{avg_red:.1f}%**\n- T_答 平均降幅：**{avg_ta_red:.1f}%**\n")
    print("PATHOLOGY_REPORT_WRITTEN", out, "n", n, "ceiling_red", round(avg_red, 1))


if __name__ == "__main__":
    main()
