# 工单分解 TICKETS.md（v0.2 · AI 代理评测版）

> 规格：SPEC.md（v0.2）。预登记 + 规格变更：logs/experiment_log.md（第 1 条预登记不可改；SPEC-CHANGE-002 = 2 开发模型 / 200 条）。
> 实现一律 test-first。【用户亲手做】步骤 AI 只备材料 + 收结果，**不代做**；用户完成前暂停依赖步骤、先推进不依赖部分。
> 状态：[ ] 待办 / [~] 进行 / [x] 完成 / [B] 外部资源阻塞 / [H] 等用户亲手做。

## 阶段 0
- [x] **T0.1** 脚手架 + venv + 依赖（v0.1 沿用，实测）。
- [x] **T0.2** 客户端 + 日志 + 熔断 + 留出锁 + responses/chat 双协议；7 单元测试；dev1/dev2/glm-5.3 冒烟 OK。
- [x] **T0.3** v0.2 规格迁移 + 预登记首条 + SPEC-CHANGE-002 + human/ 目录。

## 阶段 1
- [x] **T1.1** reading_speed.json 占位版完成（2026-11-20）：英文 238 wpm【文献 Brysbaert 2019】；中文 web 查核 Brysbaert 无中文值→待用户阶段7实测；代码/表格/列表=119、c=0 占位【推断】。每参数标来源。阶段7计时后回归重算。见 reports/reading_speed_calibration.md。

## 阶段 2
- [x] **T2.1** 抽样完成（2026-11-20，实测）：dev/test 各 100、每类 25、中文≥8（dev 15/8/10/11、test 14/15/12/8）、重叠 0、字段齐全；¥1.42。两阶段中文优先 + 重试 + 断点续跑，16/16 单测。
- [H] **T2.2** 用户抽查 40 条分类（15min）；错分 >10% 改提示词重跑。**材料已备妥** human/classification_spotcheck.html（交互判 ✓/✗ + 实时错分率 + 导出）。

## 阶段 3
- [x] **T3.1** 生成完成【实测】：200 条（dev1/dev2 各 100，0 空，字段齐），¥15.71。SPEC-CHANGE-003/005（流式+墙钟+qwen low+逐条容错）。

## 阶段 4
- [~] **T4.1** 切分 segment.py（7 单测）+ G1/G2 标注 prompt/解析/运行器 run_annotation.py + 金标分层 make_gold_set.py + κ/合并逻辑完成；金标标注网页（T4.2 材料）待做。
- [H] **T4.2** 用户金标 30 条（2.5h，四类×两模型，不看 AI 标注）→ human/gold/user/。**gold_annotation.html 已填充 30 条就绪**，待用户亲手标。
- [~] **T4.3** G1 金标（DeepSeek low，SPEC-CHANGE-006）28/30 有效；compute_calibration 就绪；**待用户金标 30（T4.2）后算 κ**≥0.6 放量。
- [ ] **T4.4** G1/G2 独立标 200（隔离会话；G2 样例打乱 + 规范措辞改写）；必留点取并集；分歧保守 留>压>删 + 清单。阻塞 T4.3。
- [H] **T4.5** 用户裁决 50 分歧单元（30min）→ 保守原则与用户一致率。**裁决网页生成器 make_adjudication_page.py 就绪**，待 G1/G2 标注+分歧清单。
- [~] **T4.6** finalize_annotations + eval/pathology.py（病理×类别×模型、时间占比、理论上限，3 单测）完成；P8/T_答 分布汇总脚本 + 实跑待校准后接 final 标注。

## 阶段 5
- [~] **T5.A** schemes/scheme_a.py 完成（6 单测）：13 规则 + 基线 + A/baseline/off + 逐条消融 build_prompt(remove=k)；批量运行接口待阶段 6 编排。
- [~] **T5.B** scheme_b.py 重组（6 单测）+ scheme_b_rewrite.py apply_scheme_B 完整流程（GLM 改写+禁用项+compress 子集校验，3 单测）完成；金标样例剔除评测待接。
- [x] **T5.C** schemes/scheme_c.py build_logit_bias 完成（2 单测）；仅适用 logit_bias 接口（百炼 Responses 不支持，dev N/A）；禁 max_tokens 截断。
- [~] **T5.F** 核心 scheme_f.py（意图分类/路由 off-light-full/句缓冲，11 单测）+ scheme_f_proxy.py 钩子 + litellm_config.yaml 完成；proxy 实跑需 litellm[proxy] + 首字延迟实测待部署。
- [ ] **T5.Aopt** DSPy/GEPA（可选，仅开发集，约束 95%/0 错误）。阻塞 T5.A、T4.6。
- [B] **T5.D/E** 权重方案（可选，需 GPU，不做不影响结论）。

## 阶段 6
- [~] **T6.1** metrics + stats + judges + aggregate（summarize 分类别×模型+CI）+ ablation + run_eval.py 编排完成；待 annotations/final + 校准后实跑。
- [H] **T6.2** 用户盲评校准 30 对（40min）→ 裁判一致率 ≥80% 采纳否则降级推断。**盲评网页生成器 make_blind_eval_page.py 就绪**，待方案输出+随机配对。
- [H] **T6.3** 用户复核 30 保留率判定（20min）+ **确认全部新增错误**。**复核网页生成器 make_retention_check_page.py 就绪**，待裁判判定+抽样。
- [ ] **T6.4** 消融：A 去规则 1–11；B 禁 move_first/compress/delete；F 去意图分类。阻塞 T6.1。
- [ ] **T6.5** eval/results.csv + eval_report（含消融 + 全部校准数字）。阻塞 T6.1、T6.2、T6.3。

## 阶段 7
- [x] **T7.1** 代码测试 GLM dev1 版【实测】：original 0.96 / A 1.0 / B 0.98，A/B 均≥original **通过**（A 提升 GLM 代码正确性）。50 题 base 测试（SPEC-CHANGE-004/006）。
- [~] **T7.2** run_transfer.py transfer_pass 判据完成（单测）；实跑待阶段 7 解锁 Kimi + test 生成 + 最优方案已定。
- [~] **T7.3** ai_reader_test.py 出题/答题三条件/grade/filter_no_text/pass≤3pp 完成（单测）；实跑待 annotations/final + 40 条抽样。
- [H] **T7.4** 用户单人计时阅读 40 条（1h，半原版/半简化，计时 + 不回看答题）→ 拟合速度/c + 实际降幅（单人初步证据）。**计时网页生成器 make_timing_page.py 已就绪**（3 单测），待 T7.3 出题 + 版本分配后填充。
- [ ] **T7.5** validation_report（四项）。阻塞 T7.1–T7.4。

## 阶段 8
- [~] **T8.1** make_report.py decide_mvp（预登记规则，6 单测）+ reports/final_report.md 骨架完成；填真实数据待阶段 6/7 + 校准。

## 关键路径
T0 → T2.1 → T3.1 → T4.1 → [H]T4.2 → T4.3 → T4.4 → [H]T4.5 → T4.6 → T5.* → T6.1 → [H]T6.2/6.3 → T7 → T8。
T1.1 / T5.A / T5.B 可并行。[H] = 用户亲手做关卡：AI 备材料后暂停依赖步骤，先推进不依赖部分。
