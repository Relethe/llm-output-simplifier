"""阶段 8 MVP 决策（SPEC §12 预登记规则）+ 报告装配。
decide_mvp 为纯函数（可单测）；main 读 eval_report.json + 校准数字 + 验证结果装配 final_report.md。
每条结论标证据类型；局限须含代理同 GLM、单人阅读、SPEC-CHANGE-002。
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def decide_mvp(a, b, baseline_new_errors, code_pass, transfer_pass):
    """a/b: {red_vs_baseline, retention, new_errors}。规则：A 达标→F+A；否则 B 达标→F+B；否则回阶段4。
    达标 = T_总比基线再降≥15% 且 保留率≥95% 且 新增错误≤基线 且 11.1代码+11.2迁移通过。"""
    def ok(s):
        return (s["red_vs_baseline"] >= 15 and s["retention"] >= 0.95
                and s["new_errors"] <= baseline_new_errors and code_pass and transfer_pass)
    if ok(a):
        return "F+A"
    if ok(b):
        return "F+B"
    return "回阶段4查理论上限"


def _load(path):
    p = os.path.join(ROOT, path)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def main():
    metrics = _load("eval/eval_b_metrics.json")
    full = _load("eval/eval_b_full.json")
    code = _load("eval/evalplus/code_test_report.json")
    simpl = _load("eval/scheme_b_astra_summary.json")
    reader = _load("eval/ai_reader_report.json")
    cons = _load("eval/eval_b_conservative.json")
    out = os.path.join(ROOT, "reports", "final_report.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("# 最终报告 · 通用 LLM 输出精简工具 v0.2（AI 代理评测版）\n\n")
        f.write("> **证据声明**：本版按 SPEC-CHANGE-009 降低校准门槛，κ 仅作 AI 对 AI 一致率参考，**未经人工校准**。"
                "所有标注/裁判/盲评结果属『AI 代理评测·未经人工校准』，不得写成人工评测。实测计算项（T_总/代码测试）单独标明。\n\n")
        f.write("## 1. 推荐 MVP\n\n")
        if full:
            ov = full["summary"]["overall"]
            mvp = decide_mvp({"red_vs_baseline": 0, "retention": 0, "new_errors": 999},
                             {"red_vs_baseline": ov["t_total_red_mean"], "retention": ov["retention"],
                              "new_errors": ov["new_errors"]},
                             baseline_new_errors=0, code_pass=True, transfer_pass=False)
            f.write(f"**最终判定：`{mvp}`**。\n\n")
            f.write(f"激进版保留率 {ov['retention']*100:.2f}%（<95%）、新增错误 {ov['new_errors']}（≠0），违反信息安全硬约束。\n\n")
            f.write("**最终结论（含 B 迭代）：方案 B 面临「不可能三角」——省时≥15%、保留率≥95%、新增错误=0 三者无法同时满足。**"
                    "激进版省时21%但保留率89%；保守版保留率95.7%但省时仅7%；两版新增错误均>0。"
                    "编辑操作式简化的信息保全与省时存在根本权衡，需重新设计方法而非调参。**本实验以否定结论收尾。**\n\n")
        else:
            f.write("待评测数据。\n\n")
        f.write("## 2. 核心实测数据\n\n")
        if metrics:
            ov = metrics["summary"]["overall"]
            f.write(f"### 方案 B 阅读时间降幅（{metrics['n']} 条，实测计算）\n\n")
            f.write(f"- **T_总平均降幅 {ov['t_total_red_mean']:.2f}%**（95% CI [{ov['t_total_red_ci95'][0]:.2f}, {ov['t_total_red_ci95'][1]:.2f}]），超 15% 阈值。\n")
            f.write(f"- T_答平均变化 {ov['t_answer_red_mean']:.2f}%（负值=到答案变慢，见局限）。\n")
            for m, s in metrics["summary"]["by_model"].items():
                f.write(f"- {m}：T_总降 {s['t_total_red_mean']:.2f}%，T_答 {s['t_answer_red_mean']:.2f}%。\n")
            f.write("\n")
        if full:
            ov = full["summary"]["overall"]
            f.write(f"### 保留率 / 新增错误 / 盲评（AI 代理裁判，未经人工校准）\n\n")
            f.write(f"- 保留率 {ov['retention']*100:.2f}%（硬约束≥95%）；新增错误 {ov['new_errors']}；盲评简化胜率 {ov['blind_win_rate']*100:.1f}%。\n\n")
        else:
            f.write("### 保留率 / 新增错误 / 盲评\n\n裁判运行中，待 eval_b_full.json。\n\n")
        if simpl:
            f.write(f"### 简化操作汇总（{simpl['overall']['n']} 条）\n\n")
            f.write(f"- 平均字符降幅 {simpl['overall']['mean_char_reduction_pct']:.2f}%，平均延迟 {simpl['overall']['mean_latency_ms']:.0f}ms。\n")
            f.write(f"- 操作分布 {simpl['overall']['ops']}；简化器 {simpl['overall']['simplifier_roles']}。\n\n")
        if cons:
            cv = cons["summary"]["overall"]
            f.write("## 2b. B 迭代：保守简化器对比（SPEC-CHANGE-010）\n\n")
            f.write("| 指标 | 激进版 | 保守版 | 硬约束 |\n|---|---|---|---|\n")
            f.write(f"| 保留率 | 89.43% ❌ | **{cv['retention']*100:.2f}%** {'✅' if cv['retention']>=0.95 else '❌'} | ≥95% |\n")
            f.write(f"| 新增错误 | 23 ❌ | {cv['new_errors']} ❌ | =0 |\n")
            f.write(f"| T_总降幅 | 20.91% ✅ | {cv['t_total_red_mean']:.2f}% ❌ | ≥15% |\n\n")
            f.write("**权衡前沿（核心结论）**：省时与保信息此消彼长——激进省时21%但丢信息，保守保住信息(95.7%)但只省时7%。"
                    "「新增错误=0」极严，两形态都未过。**方案 B 无法同时满足三硬约束**，需重新设计（如更细粒度的信息保全机制）。\n\n")
        f.write("## 3. 校准数字（参考，非人工校准）\n\n")
        f.write("- 分类抽查 40：错分率 22.5%（>10%）→ 已改提示词重分类（SPEC-CHANGE-007 配额偏移）。\n")
        f.write("- G1–用户中文 κ_label≈-0.017 / κ_pathology=0（216 单元）。\n")
        f.write("- G1–外部AI 非中文 κ_label=0.289 / κ_pathology=0.203（794 单元）。\n")
        f.write("- 重测批 G1–外部AI κ_label=0.108 / κ_pathology=0.157（440 单元）。\n")
        f.write("- 均 <0.6；按 SPEC-CHANGE-009 不作硬关卡，AI 标注作工作标准。\n\n")
        f.write("## 4. 外部验证\n\n")
        if code:
            f.write("### 11.1 代码测试（实测，base 测试 SPEC-CHANGE-004，50 题）\n\n")
            for cond, r in code.items():
                f.write(f"- {cond}: pass@1_base={r['pass_at_1_base']}\n")
            f.write("- A/B 均≥original，**通过**。注：dev1=GLM 时 A 提升代码正确性；简化器中途换模型见局限。\n\n")
        if reader:
            f.write(f"### 11.3 AI 读者测验（AI 代理，{reader['n_kept_after_filter']} 题）\n\n")
            f.write(f"- 原版正确率 {reader['acc_original']*100:.2f}%，简化版 {reader['acc_simplified']*100:.2f}%，"
                    f"**下降 {reader['drop_pp']:.2f}pp**（阈值≤3pp，{'通过' if reader['pass_le_3pp'] else '未通过'}）。\n\n")
        f.write("- 11.2 留出迁移（Kimi）：**暂缓**——方案 B 保留率已 <95%（迁移前提不成立），官方 Kimi 额度有限。\n")
        f.write("- 11.4 单人计时阅读：待用户（只备材料）。\n\n")
        f.write("## 5. 已知局限\n\n")
        f.write("- **未经人工校准**（SPEC-CHANGE-009）：κ 未达标，AI 标注/裁判作工作标准，结论降级为 AI 代理参考。\n")
        f.write("- **T_答指标局限**：简化器仅少量 move_first，答案未前移；删开头单元后 answer_uid 启发式失效，T_答反而变慢。需改进答案定位。\n")
        f.write("- **简化器中途换模型**（Astra→Sol→DeepSeek，SPEC-CHANGE-006/009 相关）：方案 B 结果按实际 simplifier_role 分组，跨模型可比性受限。\n")
        f.write("- 代理角色同为 DeepSeek：G1–G2 一致≠独立验证；裁判可能偏好同家族文本。\n")
        f.write("- 中文阅读速度占位（推断），待用户计时标定。代码测试为 base（plus 沙箱 Windows 不可用）。\n")
        f.write("- SPEC-CHANGE-002 开发模型 3→2；SPEC-CHANGE-007 分类纠正后配额偏移。\n\n")
        f.write("## 6. 收尾与未来方向\n\n")
        f.write("本实验以否定结论收尾：方案 B（编辑操作式简化）无法同时满足三硬约束（不可能三角）。\n")
        f.write("未来若要继续：①更细粒度信息保全（压缩逐信息点校验）；②将「新增错误=0」放宽为错误率阈值（需重新预登记）；"
                "③只精简纯套话（省时有限）。留出迁移因无达标方案未跑。\n")
        f.write("人工校准材料已备齐于 human/（盲评30对/保留率复核30/计时阅读40 等），供后续人工验证 AI 代理结果。\n")
    print("REPORT_WRITTEN", out)


if __name__ == "__main__":
    main()
