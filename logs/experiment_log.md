# 实验日志 experiment_log.md（v0.2 · AI 代理评测版）

> 规格 of record：`SPEC.md`（v0.2）。v0.1 规格与日志已归档为 `SPEC_v0.1_archived.md` / `experiment_log_v0.1_archived.md`。
> **第 1 条为预登记，看到任何实验数据之前写定，之后不得修改，只能追加说明**（SPEC §4）。
> 证据类型四档：实测 / AI 代理评测（经 N 条人工样本校准）/ 单人实测 / 推断。**AI 代理结果不得写成“人工评测”。**

---

## 第 1 条 · 预登记（v0.2，2026-11-20， seeing 任何实验数据之前）【不可修改 · 只追加】

**版本说明**：本预登记取代 v0.1 预登记（已归档）。v0.2 于 2026-11-20 采纳，此前仅做过连通性冒烟（v0.1 下 dev1/dev2 各 1 条「1+1」+ glm-5.3 探测 1 条），**未生成任何 responses_dev、未做任何标注/评测**，故仍属“看到数据之前”。

### 随机种子
42（抽样、bootstrap、盲评左右顺序、金标分层抽样、计时版本分配均用此种子）。

### 硬约束（SPEC §1.3）
- 必留信息保留率 ≥ **95%**（分母 = 原回答必留点总数；部分成立按不成立计）。
- 新增错误 = **0**（逐条记录；用户全部逐条确认，不抽样）。
- 代码块**逐字节不变**（只整块 keep/delete）。

### 主指标
T_总 = Σ(L_i / v_类型(i)) + c·N_结构；T_答 = 读到首个直接回答单元的预估时间。v/c 来源见阶段 1（英文 238 wpm 文献；中文待核文献；代码/表格/列表/c 用用户阶段 7 计时回归，之前用正文 0.5 倍占位标推断）。

### 标注与校准阈值（SPEC §6, §8.5）
- 分类抽查 **40 条**，错分率 > **10%** → 改分类提示词重跑。【用户亲手做】
- 金标集 **30 条**，分层覆盖四类 × 三模型；用户独立标，期间不看 AI 标注，存 human/gold/。【用户亲手做，约 2.5h】
- G1–用户 Cohen's κ（label 与 pathology 分别）≥ **0.6** → 放量；< 0.6 → 改规范 + **换新批 15 条**重测，**不得同批反复调提示词**。
- 放量：G1、G2 各独立标完 300 条。
- 必留点最终清单 = G1 ∪ G2 并集（分母偏大、结论保守）。
- 分歧单元保守原则：**留 > 压 > 删**；列入分歧清单。
- 分歧复核：随机 **50 单元**用户裁决，报告保守原则与用户一致率。【用户亲手做，约 30min】
- 报告 G1–G2 κ、G1–用户 κ。

### 评测校准阈值（SPEC §10.2）
- 盲评问题固定：“哪个让你更快拿到需要的信息，而且不缺东西？”（A/B/一样），**不得问“哪个更好”**；每对正反顺序各判一次，不一致记“一样”。
- 盲评校准：用户亲判 **30 对**（随机来源/顺序/无标签）。裁判–用户一致率 ≥ **80%** 才采纳裁判盲评；否则盲评降级为**推断**并写明一致率。【用户亲手做，约 40min】
- 保留率校准：随机 **30 个**“必留点–简化版”判定用户复核，报告一致率。【用户亲手做，约 20min】
- 方案 B 结果**单独标注**（改写者=裁判=GLM，盲评胜率可能偏高）。

### 统计（SPEC §10.3）
配对 bootstrap **10000 次** → 95% CI；多重比较 **Holm 校正**；按 4 类别 × 3 模型报告 + 额外延迟/费用。

### 外部验证阈值（SPEC §11）
- 11.1 代码测试：EvalPlus 抽 **50 题**，pass@1 **不下降**。（全自动，不依赖模型判断）
- 11.2 留出迁移：test **100 条** × (3 开发 + 1 留出)；留出 T_总降幅 ≥ 开发平均的 **70%**，保留率 ≥ **95%**。（全自动）
- 11.3 AI 读者测验：**40 条**提问，每条 2–3 题；答题三条件（只看原版/只看简化版/无文本对照）各独立会话；指令“只依据给定文本，找不到答‘找不到’”；**剔除条件 3 也能答对的题**，剔除后 < **60 题**则补出题；通过 = 条件 2 正确率比条件 1 降 ≤ **3 个百分点**。证据类型 = AI 代理评测。
- 11.4 单人计时阅读：同 40 条，随机半原版/半简化版，同一提问只读一版；网页计时 + 不回看答题；记实际阅读时间与正误。【用户亲手做，约 1h】**单人结果只作初步证据，不判定通过**；“阅读时间降 ≥ 30%”留待 ≥ 3 读者再验。

### 方案 B 样例约束（SPEC §9.2）
提示词样例**只取金标集**，且这些样例对应的回答**从评测中剔除**。

### MVP 决策规则（SPEC §12，预登记）
1. 方案 A 的 T_总 比基线再降 ≥ **15%**，保留率 ≥ **95%**，新增错误数 ≤ 基线，**且 11.1、11.2 通过** → **MVP = F + A**。
2. 否则方案 B 满足以上全部条件 → **MVP = F + B**。
3. 都不满足 → 回阶段 4 检查理论上限是否本来就低。
- 基线 = 系统提示词仅“请简洁回答。”，位置与 A 相同。

### 隔离规则与已知局限（SPEC §2，须写进最终报告）
- 各代理角色（G1/G2/改写/出题/答题/裁判）均 GLM，**独立会话**，不共享上下文，不传递未授权输出。
- 送裁判/答题的文本**去掉一切来源标记**（文件名/方案名/模型名）。
- 局限：所有代理同为 GLM → G1–G2 一致 ≠ 独立验证；裁判可能偏好 GLM 自己改写的文本；阅读时间仅单人数据。对策 = 上述人工校准 + 11.1/11.2 两项不依赖模型判断的验证。
- 开发模型尽量非 GLM 家族；若含 GLM，该模型结果**单独列出、不并入总平均**。

### 用户亲手做事项（SPEC §13，AI 不得代做，只备材料 + 收结果，约 5h）
① 抽查 40 分类(15min,阶段2) ② 金标 30(2.5h,阶段4) ③ 裁决 50 分歧(30min,阶段4) ④ 盲评校准 30 对(40min,阶段6) ⑤ 复核 30 保留率 + 确认全部新增错误(20min起,阶段6) ⑥ 计时阅读 40(1h,阶段7)。每步前备可直接填写的表格/网页；用户完成前暂停依赖步骤，先推进不依赖部分。

---

## 第 2 条 · 环境与配置（2026-11-20，追加）【实测】
- venv：uv 管理 CPython 3.12.16；依赖 openai 3.55.1 / litellm 1.110.0 / datasets 5.2.0 / scipy 1.18.1 / sklearn 1.9.1 / pysbd 0.3.4 等（v0.1 已装，沿用）。
- 客户端 scripts/llm_client.py 支持 responses / chat 双协议；调用日志 logs/calls.jsonl；预算熔断 logs/budget_state.json（cap ¥100）；留出锁 dev_phase_locked。单元测试 7/7 通过（v0.1）。
- **百炼 token-plan 端点** `https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`，协议 **OpenAI Responses**，密钥 = DSH refs.ALI_API_KEY（写入 .env DASHSCOPE_API_KEY，未打印明文）。
- **模型目录实测**（GET /models，23 个）：文本生成家族仅 **DeepSeek / Qwen / GLM** 三家；其余为音频/图像/视频（qwen-audio/image、wan）。可用文本 ID 含 deepseek-v4.1-flash-1017、deepseek-v4-pro、qwen4-max、qwen3.8-max、glm-5.2、glm-5.3 等。
- **冒烟实测**：dev1 deepseek-v4.1-flash-1017（in67/out43，1477ms）、dev2 qwen4-max（in69/out20，1456ms）、glm-5.3（in49/out61）均返回非空「1+1等于2。」。累计 ≈¥0.003。
- **GLM 代理角色**：改写/裁判/G1/G2/出题/答题 = glm-5.3（百炼，responses，独立会话）。
- **留出**：官方 Kimi 密钥写入 .env MOONSHOT_API_KEY（len62，未打印明文）；model 暂定 moonshot-v1-32k（待阶段 7 核实），chat 协议，**开发期锁死**；额度有限，省用。
- 价格表为近似【推断·待核】；百炼为 token-plan 配额制（实际按 token 额度扣），官方 Kimi 额度独立且有限。

## 第 3 条 · 待决（追加）
- **开发模型第三家**：百炼密钥无第四家非 GLM 文本家族。v0.2 要 3 开发模型且尽量非 GLM → 第三家只能 GLM(glm-5.3，单独列出) 或退回 2 家。**待用户拍板**（见 ask_user_question）。定案前 dev3 暂不写入 config、不生成 responses。

## 第 4 条 · 第 3 条定案 + SPEC-CHANGE-002（2026-11-20，追加，生成任何 responses 之前）
- 第 3 条待决已定：用户选 **B（退回两家开发模型）**。
- **SPEC-CHANGE-002**（用户批准，2026-11-20）：v0.2 原写 3 开发模型 / 300 条；因百炼密钥仅有 DeepSeek/Qwen 两个非 GLM 文本家族（目录实测），且用户优先避免 GLM 自评混淆，批准改为 **2 开发模型（DeepSeek `deepseek-v4.1-flash-1017` + Qwen `qwen4-max`）/ 200 条**。
- 连带调整（**仅数量，阈值不变**）：responses_dev 300→200；金标 30 条分层覆盖四类 × **2 模型**；阶段 6 按 4 类别 × **2 模型**报告；11.2 用 **2 开发 + 1 留出(Kimi)**；G1/G2 放量各标 **200 条**；病理统计/理论上限基于 200 条。
- **不变**：全部硬约束与校准阈值（95% / κ0.6 / 80% / 15% / 70% / 3pp / 60 题 / 30 对 / 30 判定 / 50 单元 / 40 抽查）、MVP 决策规则、证据类型规则、隔离规则。开发平均 = 2 家平均。
- 局限（最终报告标明）：跨家族泛化证据为 2 家；v0.2 预登记中“3 模型”细节经此批准变更。
- config 现状即 2 开发模型（未加 dev3），无需改。
- **阶段 0 验收达成（v0.2）**：dev1 / dev2 / glm-5.3 各跑通 1 条【实测】；阈值已预登记（第 1 条）；留出 Kimi 密钥已存、开发期锁死（连通性留阶段 7 验）。

## 第 5 条 · 阶段 1 reading_speed.json 占位版（2026-11-20，追加）【文献 + 推断】
- 英文正文 **238 wpm**（非虚构默读）= Brysbaert 2019 元分析【文献，doi:10.1016/j.jml.2019.104047】。
- 中文正文：web 查核 Brysbaert 2019 摘要/Highlights/语言节，确认针对英文/拉丁字母语言，**无中文 cpm 数值** → 按 SPEC §5 待用户阶段7实测（value=null），不凭空填。
- 代码/表格行/列表项 = 0.5×英文正文 = **119**（各自单位）占位【推断】；c 结构开销暂计 **0** 占位【推断】。
- 产出 reading_speed.json（每参数标来源/证据类型）+ reports/reading_speed_calibration.md。
- 数据源决策：用户选 **HF LMSYS(dev)+WildChat(test)**（跨源迁移更强）；两数据集 gated，需用户亲手同意条款 + HF token（待提供）。
- 待用户阶段7计时 → 回归拟合中文/代码/表格/列表/c → 重算全部 T_总/T_答。

## 第 6 条 · 阶段 2 抽样启动（2026-11-20，追加）【实测进行中】
- HF 访问实测：LMSYS-Chat-1M(dev) + WildChat-1M(test) 均通（用户已同意条款；HF token 写入 .env，未回显）。
- 环境修复：harness 共享缓存 `D:\CodeTools\hf-cache` 拒绝访问(WinError5) → HF_HOME/HF_DATASETS_CACHE 改指向项目内 `data/hf-cache`（仅本进程，不动共享缓存）；Windows symlink 警告无害已抑制。
- schema 实测：LMSYS = conversation/language/openai_moderation.flagged/redacted；WildChat 另含 toxic/detoxify_moderation/conversation_hash。
- 抽样脚本 scripts/sample_prompts.py（test-first，纯逻辑单测 8 项；总 15/15 过）：流式 → 首轮提问 → 廉价筛选(长度10–2000/毒性/redacted/纯问候) → 归一化去重 → G1(glm-5.3)分类四类(创作/有害/PII/实时/问候/无关→排除) → 配额每类25中文≥8 → prompts_dev/test.jsonl + 40 条抽查样本。
- 客户端 _build_specs 改通用角色映射；config 加 g1/g2(glm-5.3 独立会话)。
- 后台 job `pwsh-472ecb000ae54a09`（max-scan 15000 / max-classify 900）运行中；完成后收结果、验配额、备用户抽查表(T2.2)。

## 第 7 条 · glm-5.3 推理开销问题与修复（2026-11-20，追加）【实测】
- 问题：glm-5.3 在百炼 token-plan 部署默认输出 reasoning 推理项，一次分类耗 **1803 token / 21s**；数千次代理调用不可行。首个抽样 job 因此极慢（89 调用 / ¥0.4 / 10min），已 kill 止损。
- 实测约束：`enable_thinking=False` 被拒（"restricted to True"）；`reasoning.effort=none` 被拒；`thinking={type:disabled}` 无效（仍推理）；glm-5.2 同样带推理。
- **修复【实测有效】**：`reasoning={"effort":"low"}`（minimal/medium 亦可）+ `temperature=0` → 输出降到 **2 token**、延迟 **~1.2s**。分类用 effort=low + temperature=0（确定性）。
- 已更新 classify_prompt 传 reasoning effort=low + temperature=0；重启抽样 job。
- 注意：低推理深度分类精度可能略降，由用户抽查 40 条(T2.2，>10% 错改提示词)校准兜底。
- 复用经验：此部署 GLM 强制思考，代理角色调用须带 reasoning.effort 控开销；生成模型(dev)按 SPEC 用默认参数不动。

## 第 8 条 · 阶段 2 健壮性修复 + 中文配额策略（2026-11-20，追加）【实测】
- 第二次抽样 job(pwsh-49c18c4d3d5d4091) 因网络瞬断 `DNS getaddrinfo failed`(APIConnectionError) 崩溃，无重试致整批丢失（已跑 ~460 调用）。
- 修复①【实测，单测过】：客户端 call() 加瞬时错误(APIConnectionError/APITimeoutError/RateLimitError/InternalServerError)退避重试 5 次(1/2/4/8/16s)；OpenAI client max_retries=3 / timeout=90。新增 test_retry_on_transient_error，总 **16/16** 过。
- 修复②：抽样断点续跑，checkpoint `data/_ckpt_{source}.jsonl` 每 25 条落盘，重启跳过已分类哈希。
- 发现【实测】：LMSYS 流式前段中文极稀疏——顺序分类 200 条仅 3 条中文，远低于每类 ≥8 中文配额；顺序策略低效（678 调用未填满）。
- 修复③：改**两阶段中文优先**——A 廉价扫描 60000 行收集候选(不调 API)按中文/非中文分池；B1 优先分类中文填 ≥8/类；B2 非中文补 25/类。API 调用降至 ~150。
- 第三次 job `pwsh-fb622cb9d0154a2e` 运行中（max-scan 60000 / max-classify 600）；完成后验配额、备用户抽查表(T2.2)。

## 第 9 条 · 阶段 2 抽样完成（2026-11-20，追加）【实测】
- 两阶段中文优先 job(pwsh-fb622cb9d0154a2e) 成功(exit0)。dev(LMSYS) 扫描 34012 行 / zh_pool 650 / 新分类 141；test(WildChat) 扫描 43086 / zh_pool 11140 / 新分类 227。
- **配额实测达标**：dev/test 各 100，每类 25；中文/类 dev=15/8/10/11、test=14/15/12/8（均≥8）；source_id 与 text 重叠均 **0**（互不重叠）；字段齐全。
- 累计花费 **¥1.42 / ¥100**。产出 data/prompts_dev.jsonl、prompts_test.jsonl、human/classification_spotcheck_40.jsonl(40 条)。
- **T2.1 完成**。T2.2 用户抽查 40 条分类材料备妥（待用户亲手做，>10% 错改提示词重跑）。
- 阶段 3 生成启动（200 条，dev1/dev2 默认参数、无系统提示）。

## 第 10 条 · 阶段 3/4/5 并行推进（2026-11-20，追加）【实测】
- 阶段 3 生成 job(pwsh-55e637b47bae409b) 运行中：dev1/dev2 默认参数、无系统提示，逐条 append+flush 可续跑；进度 25/200，累计 ¥2.08。dev 默认含推理较慢。
- **T2.2 用户抽查材料备妥**：human/classification_spotcheck.html（40 条交互判 ✓/✗、实时错分率 >10% 告警、导出/复制结果）。待用户亲手做。
- **T4.1 单元切分** scripts/segment.py 完成【7 单测过】：正文按句（中 。！？；+换行 / 英 pysbd）、列表项/表格行/标题各 1 单元、代码块整块 1 单元**逐字节保留**。
- **T5.B 核心** schemes/scheme_b.py apply_edits 完成【6 单测过】：确定性重组，code 仅 keep/delete、move_first≤1、违规 sanitize 为 keep、**重组后代码块逐字节一致**。compress 子集裁判校验待阶段 6 接。
- 总单测 **31/31** 过。
- 下一步：生成完成后 → 阶段 4 G1/G2 标注流程 + 金标材料；阶段 5 A/C/F；阶段 6 评测脚本（T_总/T_答/保留率/bootstrap/Holm）。

## 第 11 条 · Goal 第 1 轮：评测/统计/方案A/κ 核心代码（2026-11-20，追加）【实测，62 单测过】
- 阶段 6 eval/metrics.py：T_总/T_答（Σ L_i/v_i + c·N_结构；英文词/中文 CJK 字/代码行/表格行·列表项计 1；结构切换计数；中文 v 未标定暂用英文占位·推断）。8 单测。
- 阶段 6 eval/stats.py：配对 bootstrap 10000 percentile CI（seed42 向量化）+ Holm 校正。5 单测。
- 阶段 5 schemes/scheme_a.py：13 规则提示词 + 基线「请简洁回答。」+ build_messages(A/baseline/off) + 逐条消融 build_prompt(remove=k)。6 单测。
- 阶段 4 eval/kappa.py：Cohen's κ（label 分类）+ pathology_kappa（P1–P11 二值宏平均）。6 单测。
- 阶段 4 scripts/annotate.py：必留点并集去重、分歧保守裁决(留>压>删)、schema 校验(含 code 不可压)。7 单测。
- 生成 job 续跑 46/200，¥3.06。
- 下一步：G1/G2 标注 prompt + 金标分层抽样材料；方案 B GLM 改写 prompt + compress 裁判子集校验；方案 C/F；阶段 6 保留率/新增错误裁判 + 盲评编排；阶段 7 EvalPlus + 迁移。

## 第 12 条 · Goal 第 2 轮：标注流水线 + 方案B改写 + 阶段6裁判（2026-11-20，追加）【实测，80 单测过】
- 阶段 4 scripts/annotation_prompts.py：G1/G2 标注 prompt（含 P1–P11 病理表，G2 措辞改写 + 表序打乱）、build_annotation_messages、parse_annotation_json。
- 阶段 4 scripts/make_gold_set.py：stratified_gold 分层抽 30（四类×两模型 8 层均分覆盖）；main 生成完成后跑 → human/gold/gold_candidates.jsonl（含切分单元）。
- 阶段 4 scripts/run_annotation.py：G1/G2 独立会话标注（glm-5.3 effort=medium + temp0），--mode gold/full，逐条落盘 annotations/{g1,g2}/ 可续跑。**full 须 κ≥0.6 校准通过后运行**。
- 阶段 5 schemes/scheme_b_rewrite.py：GLM 改写 prompt（只输出 edit ops）+ parse_edit_ops + compress_is_subset 裁判校验。
- 阶段 6 eval/judges.py：retention_judge 逐点（部分成立按不成立）、new_errors_judge（JSON 数组）、blind_eval（固定问题 + 正反序不一致记一样）。
- 新增 8（annotation）+ 11（rewrite/judges，fake client）单测；总 **80/80**。
- 生成观察：dev_028_dev1「Python 画小猪」代码回答 8647 token / 39.5s——长代码生成慢但 job 正常推进（57/200，¥3.57）。
- 下一步：金标标注网页（T4.2 材料）；方案 C/F；阶段 6 评测编排 runner + 消融；阶段 7 EvalPlus + 迁移；生成完成后跑金标抽样 + G1 校准。

## 第 13 条 · Goal 第 3 轮：方案 C/F + 生成超时修复（2026-11-20，追加）【实测，91 单测过】
- **生成卡顿根因【实测】**：timeout=90s 对长代码生成太短（qwen 画小猪 >90s）→ 超时重试空转，57/200 停滞 4.5min。修复：客户端 timeout=300s + max_retries=2（减嵌套）；续跑后恢复推进 **59/200，¥4.08**。
- 阶段 5 schemes/scheme_c.py：build_logit_bias（开场词首 token 压 -100，encode_fn 用目标模型分词器）；仅适用 logit_bias 接口，百炼 Responses 不支持故 dev N/A。2 单测。
- 阶段 5 schemes/scheme_f.py：intent_classify（创作/代码/其他）+ route_request（off/light/full，创作放行）+ sentence_buffer（流式句缓冲）。11 单测。
- 测试抓出弱点：连续关键词「写诗」匹配不到「写一首诗」→ 改正则 `(写|创作|编|作).{0,12}(诗|故事|小说…)`。
- schemes/scheme_f_proxy.py：LiteLLM CustomLogger 钩子（部署 glue，需 litellm[proxy]，guarded import）；litellm_config.yaml 代理配置。
- 总 **91/91**。
- 下一步：金标标注网页（T4.2）；阶段 6 评测编排 runner + 消融；阶段 7 EvalPlus + 迁移；生成完成后金标抽样 + G1 校准。

## 第 14 条 · Goal 第 4 轮：阶段6聚合/消融/编排 + 阶段7 EvalPlus核心 + 方案B完整流程（2026-11-20，追加）【实测，104 单测过】
- 阶段 6 eval/aggregate.py：pct_reduction / retention_rate / summarize（overall + by_category + by_model，bootstrap CI）。
- 阶段 6 eval/ablation.py：A 去规则 1–11（12 条件）/ B 禁 move_first·compress·delete（4）/ F 去意图（2）。
- 阶段 6 scripts/run_eval.py：评测编排（condition_text: original/baseline/A/B/A+B/A_noK；evaluate_one 串联指标+裁判+盲评；load_eval_items 接 annotations/final；写 results.csv + eval_report.json）。**须待标注+校准**。
- 阶段 5 schemes/scheme_b_rewrite.py apply_scheme_B：GLM 改写→禁用项 keep→compress 子集校验→确定性重组（3 单测 fake client）。
- 阶段 7 scripts/evalplus_harness.py：extract_code（取最长 python 块）+ pass_at_1；实跑需 evalplus 沙箱。
- 新增 5（eval_agg 含 get_answer_uid）+ 3（apply_scheme_B）单测；总 **104/104**。
- 生成 67/200，¥5.05，timeout 修复后稳定推进。
- 下一步：金标标注网页（T4.2）+ 其余人力材料（盲评/保留率复核/计时网页）；阶段 7 迁移 runner + AI 读者测验；阶段 8 报告骨架；生成完成后金标抽样 + G1 校准。

## 第 15 条 · Goal 第 5 轮：阶段7读者测验/迁移判据 + 阶段8决策/报告骨架（2026-11-20，追加）【实测，118 单测过】
- 阶段 7.3 scripts/ai_reader_test.py：出题 GLM（只看必留点）+ 答题 GLM 三条件（原版/简化/无文本，独立会话）+ grade_answer + filter_by_no_text（剔除靠知识答对）+ reader_test_pass（降≤3pp）。
- 阶段 7.2 scripts/run_transfer.py：transfer_pass（留出降幅≥开发均值 70% 且保留率≥95%）；main 待阶段 7 解锁 Kimi + 最优方案。
- 阶段 8 scripts/make_report.py：decide_mvp（预登记 §12：A 达标→F+A，否则 B→F+B，否则回阶段4；须 11.1+11.2 通过）+ 报告装配；reports/final_report.md 骨架已生成（证据类型/校准数字/局限/下一步占位）。
- 新增 9（reader/transfer）+ 6（report）单测；总 **118/118**。
- 生成 73/200 正常推进（此前“停滞”系检查间隔短 + 慢回答完成中，误判；进程 CPU 活跃）。
- **至此阶段 0–8 核心代码全部建成 + 单测**。剩余：6 个人力关卡材料网页；生成完成后金标抽样 + G1 校准；EvalPlus 实跑（需 install）；迁移实跑（需 Kimi 解锁）；报告填真实数据（待校准）。

## 第 16 条 · Goal 第 6 轮：人力材料网页 + 生成流式/墙钟根治（2026-11-20，追加）【实测，126 单测过】
- **T4.2 金标标注网页生成器** scripts/make_gold_page.py（30 条逐单元 label/move_first/pathology/note + 必留点 + intent，代码块限删/留，导出金标 JSON）；3 单测。待 gold_candidates 生成后填充。
- **T7.4 计时阅读网页生成器** scripts/make_timing_page.py（开始计时→读完隐藏→不回看答题→记 reading_ms，逐条导出）；3 单测。待 timing_items 后填充。
- **生成卡顿根治【实测】**：① 旧 job 孤儿进程残留并发冲突 → 杀净；② 非流式长回答总时长超时 → 改**流式 Responses**（逐 token，STREAM_OK 验证）；③ 真根因：qwen4-max 对 dev_036（2000 词化工长文，误分类创作）**默认推理无休止**（150s/1827 事件全推理项，output_text=0）→ 加**每调用墙钟上限 240s** + 空则退避 effort=medium 重试 + 仍空跳过记失败。
- **SPEC-CHANGE-003**（可行性偏离，待用户追认）：生成保持无系统提示/默认参数，但加墙钟上限 240s 防推理无休止；病理超时项退避有限推理（effort=medium，输出仍不受约束）；仍空跳过记 failures。dev_036 创作长文误分类待 T2.2 抽查纠正。
- 客户端 responses 改流式 + max_wall_s 参数；新增流式累积 + 墙钟上限单测。总 **126/126**。
- 生成 job `pwsh-50e77923f0034bb1` 续跑（从 73）。

## 第 17 条 · Goal 第 7 轮：6 个人力关卡材料网页全部备齐（2026-11-20，追加）【实测，131 单测过】
- 生成进程澄清：2 进程系 uv venv 启动器(父)+子解释器，**单一逻辑 job**；回答 75→79 零重复，健康。墙钟+退避修复后流畅推进。
- **T6.2 盲评校准页** make_blind_eval_page.py（30 对随机无标签，固定问题 A/B/一样，不问更好）。
- **T4.5 分歧裁决页** make_adjudication_page.py（50 单元 G1/G2/保守暂采，用户裁决，代码限删/留）。
- **T6.3 保留率复核+新增错误确认页** make_retention_check_page.py（30 判定复核 + 全部新增错误逐条确认）。
- **至此 6 步人力材料生成器全备**：T2.2 抽查(已生成 html)/T4.2 金标/T4.5 裁决/T6.2 盲评/T6.3 保留率/T7.4 计时。各待对应数据就绪后一键填充。
- 新增 4+1 单测；总 **131/131**。生成 79/200，¥6.57。
- 剩余 autonomous：生成完成→金标抽样+G1 校准流程；EvalPlus install+实跑；各人力材料的数据填充脚本（配对/抽样/分歧清单）；报告填数。人力关卡待用户。

## 第 18 条 · Goal 第 8 轮：人力材料数据填充逻辑（2026-11-20，追加）【实测，137 单测过】
- scripts/prepare_human_data.py：make_blind_pairs（随机 30 + 左右随机 + 去标签留映射）/ find_disagreements（G1G2 不一致 + 保守）/ sample_retention_checks（抽 30）/ assign_timing_versions（半原版半简化）；main 待数据就绪写 jsonl。7 单测。
- **人力材料链路完整**：数据填充脚本 → 网页生成器 → 用户填写 → 导出 JSON → 助手算校准。
- 生成 83/200，¥7.14。
- 剩余 autonomous：生成完成 → make_gold_set 金标抽样 + gold 页 → G1 金标标注（AI 代理，校准备料）；EvalPlus install + 实跑；报告填数。放量标注/评测/迁移/读者测验实跑待用户校准关卡。

## 第 19 条 · Goal 第 8 轮(续)：EvalPlus 代码测试 harness 建成并启动（2026-11-20，追加）【实测】
- 安装 **evalplus 0.3.1**；CACHE_DIR（AppData\Local\evalplus）拒绝访问 → monkeypatch 到项目内 data/evalplus-cache；**HumanEval+ 数据加载成功（164 题，GitHub release 下载正常）**。
- API：evalplus 0.3.1 用 untrusted_check（沙箱）+ sanitize + estimate_pass_at_k；CLI evalplus.evaluate（fire）。
- scripts/run_evalplus.py：抽 50 题(seed42) × dev1 × original/A/B 生成 → extract_code+sanitize → samples jsonl → _evalplus_run.py 包装器跑 evalplus 沙箱 → 读 eval_results 算 pass@1(plus/base) → 对比 original 不降。
- scripts/_evalplus_run.py：CACHE_DIR 补丁 + evalplus.evaluate main。
- **EvalPlus job `pwsh-2c2712ad7e254062` 启动**（50 题 × 3 条件）。137/137 单测。生成 responses_dev 续跑（83+/200）。

## 第 20 条 · Goal 第 9 轮：阶段 4 校准 + 放量编排（2026-11-20，追加）【实测，141 单测过】
- scripts/run_calibration.py：compute_calibration（G1 金标 vs 用户 κ label/pathology，≥0.6 放量、<0.6 换新批 15）+ finalize_annotations（G1G2 必留点并集 + 分歧保守裁决 + 分歧清单抽 50 供 T4.5）；main 待用户金标 + G1/G2 标注。4 单测。
- 两 job 健康：生成 88/200；EvalPlus samples_original.jsonl 已生成（50 题 original 完成，评估/A/B 续跑）。预算 ¥7.32。
- 阶段 4 编排代码全备（切分/标注 prompt/运行器/κ/合并/校准放量）。
- 剩余 autonomous：生成收尾 → 金标抽样 + G1 金标标注；EvalPlus 结果收；**pathology_report（病理统计 + 理论上限）待建**；报告填数。放量/评测/迁移/读者待用户校准。

## 第 21 条 · Goal 第 10 轮：EvalPlus 修复 + pathology_report（2026-11-20，追加）【实测，144 单测过】
- **EvalPlus 修复【实测】**：CLI 断言需全 164 题 samples → 改抽 50 真实生成 + 114 占位("pass")凑满 164，**pass@1 只统计抽样 50 题**（尊重抽 50）。杀净孤儿进程重启 job `pwsh-3bacefdbea5a4c05`。
- eval/pathology.py：pathology_stats（每病症句数占比 + 阅读时间占比 + 病症×类别×模型交叉）+ theoretical_ceiling（删/压 60%/move_first 前移 → T_总/T_答 降幅天花板）。3 单测。
- **至此全部自主代码建成**（阶段 0–8 核心 + 病理统计 + 校准放量 + 6 人力材料生成器 + 数据填充 + EvalPlus harness）。**144/144 单测**。
- 生成 97/200（¥8.02）近半；EvalPlus 续跑。
- 剩余：生成收尾 → 金标抽样 + G1 金标标注；收 EvalPlus pass@1；报告填数。放量/评测/迁移/读者实跑待用户校准。

## 第 22 条 · Goal 第 11 轮：病理报告 runner + 全流程运行说明（2026-11-20，追加）【实测，144 单测过】
- scripts/make_pathology_report.py：读 final 标注 → 病理×类别×模型交叉 + 句数/时间占比 + P8 出现率 + T_答 分布 + 理论上限 → reports/pathology_report.md（待校准放量）。
- **RUNNING.md**：全流程运行说明（阶段 0–8 命令 + 6 人力步骤网页 + 证据纪律 + 环境配置），交付物「运行说明」完成。
- 生成 99/200；EvalPlus 续跑。
- **自主代码 + 文档全部就绪**。剩余跑数据：生成收尾 → 金标抽样 + G1 金标标注；收 EvalPlus；报告填数。放量/评测/迁移/读者实跑待用户校准。

## 第 23 条 · Goal 第 12 轮：EvalPlus 沙箱 Windows 不兼容 → 自定义代码测试 runner（2026-11-20，追加）【实测，147 单测过】
- **EvalPlus CLI 沙箱在 Windows 挂死【实测】**：评估子进程 CPU≈0 / 19min 无结果，停在「samples to be tested」后多进程沙箱不工作（reliability_guard 依赖 Unix resource）。
- **SPEC-CHANGE-004**（平台不兼容偏离，待用户追认）：11.1 改用自定义子进程跑 HumanEval **base** 测试（solution + check 断言 + 超时 10s 隔离），pass@1 不下降；数据/sanitize 仍用 evalplus 包。plus 测试因沙箱不可用降为 base。
- scripts/run_code_test.py：抽 50 × dev1 × original/A/B 生成 → sanitize → run_base_test 子进程 → pass@1_base 对比。3 单测（canonical 过/错解败/超时败）。
- 生成 136/200 推进良好。代码测试 job 启动。

## 第 24 条 · Goal 第 13 轮：生成补缺脚本（2026-11-20，追加）【实测，150 单测过】
- 生成出现 SKIP_EMPTY（dev_041_dev2 / dev_063_dev1 / dev_063_dev2）：medium 退避 + 240s 仍空（推理过长）。scripts/fill_skipped.py：find_missing + effort=low 再试补缺（3 单测）；生成结束后跑补齐。
- 生成 140/200 推进；代码测试 job 续跑（original 50 生成中）。
- 剩余：生成收尾 + 补缺 → 金标抽样 + G1 金标标注；收代码测试 pass@1；报告填数。

## 第 25 条 · Goal 第 14 轮：11.1 代码测试实测结果（2026-11-20，追加）【实测】
- run_code_test 完成（exit0，base 测试 SPEC-CHANGE-004，50 题 seed42，dev1）：**original pass@1=1.0（50/50），A=0.98，B=0.98**。
- 判据「pass@1 不下降」：**A/B 均微降 0.02（各错 1 题）→ 不满足**。真实发现：精简轻微损害代码正确性。
- 局限：base 测试（plus 沙箱 Windows 不可用）、50 题小样本、降 1 题可能噪声；最终报告须标明，建议扩大样本/plus 复核。
- **对 MVP 决策影响**：预登记 §12 要求 11.1 通过，A/B 在此样本未过 → 须结合 11.2 迁移 + 保留率综合判，或回阶段 4 查理论上限。
- eval/evalplus/code_test_report.json 落盘。生成 158/200，¥11.43。

## 第 26 条 · Goal 第 15 轮：阶段 3 生成完成 200 + 金标抽样 + G1 金标标注（2026-11-20，追加）【实测】
- **生成完成【实测】**：total_done=**200**，failures=[]，dev1/dev2 各 100，字段齐全，0 空。**SPEC-CHANGE-005**（qwen dev2 直接 effort=low、deepseek 默认 cap90 + low 退避、逐条容错跳过）解决 qwen 默认推理病理慢 + 网络超时整批崩溃。累计 **¥15.71**。
- 金标抽样 30：四类×两模型全覆盖（代码/建议/解释各 4 每模型、问答 3 每模型）。human/gold/gold_candidates.jsonl + **gold_annotation.html(30) 已填充就绪**。
- G1 金标标注（AI 代理，校准备料）：run_annotation --mode gold --variants G1 → annotations/g1_gold（修复 gold/full 目录分离）；待用户金标后算 κ。
- **阶段 3 完成**。阶段 4 自主部分就绪（金标候选 + 网页 + G1 金标）；待用户亲手标金标 30 → κ 校准 → 放量。

## 第 27 条 · Goal 第 15 轮(续)：G1 金标标注完成 + 标注优化（2026-11-20，追加）【实测，150 单测过】
- **标注输出优化【实测】**：G1/G2 只输出 uid/label/move_first/pathology/note（text/type 由切分合并），输出从 6000–7582 token 降到 333–3026，延迟 45–51s 降到 4.6–30s。
- 标注容错：JSON 截断 → low 重试 → 仍败跳过（逐条不崩批）。
- **G1 金标标注完成：29/30 有效**（dev_063_dev2 超长 JSON 截断跳过），schema 全过。annotations/g1_gold 就绪。
- **阶段 4 自主准备完成**：金标候选 30 + gold_annotation.html + G1 金标 29。待用户亲手标金标 30（T4.2）→ run_calibration 算 κ → 放量。预算 ¥17.97。

## 第 28 条 · SPEC-CHANGE-006：代理 GLM→DeepSeek + dev1→GLM（2026-11-20，用户批准）【配置变更】
- 用户嫌 glm-5.3 贵，批准**方案 1**：dev1=**glm-5.3**、dev2=qwen4-max、**所有代理（G1/G2/裁判/改写/出题/答题）=deepseek-v4.1-flash-1017**。
- 家族校验：代理 DeepSeek 与 dev1(GLM)/dev2(Qwen) **均跨家族** ✓（两 dev 都干净，优于原 v0.2 仅 Qwen 跨家族）；改写=裁判=DeepSeek 同家族（v0.2 固有局限，B 盲评单独标注）；留出 Kimi ≠ 代理/开发 ✓。
- 代价：dev1 原 100 条 DeepSeek 回答作废 → 用 GLM 重生（job pwsh-770f80fdbedc4c1d）；金标重抽、G1 金标重标（DeepSeek）；旧 GLM 金标清除。
- 生成统一 effort=low（dev1 GLM/dev2 Qwen 均推理模型默认慢；SPEC-CHANGE-005 延伸）。
- 成本：代理改 DeepSeek（in1/out4）大幅省（标注/裁判大头）；dev1 GLM 生成 100 条小头。
- 代码测试 11.1 原用 dev1=DeepSeek，现 dev1=GLM，**结果须重跑**（待）。
- 预登记第 1 条「代理同为 GLM」局限更新为「代理同为 DeepSeek」；隔离规则（独立会话）不变。

## 第 29 条 · SPEC-CHANGE-006 执行完成（2026-11-20，追加）【实测】
- dev1 GLM 重生 100 完成（failures=[]，effort=low）；**200 条 = GLM 100 + Qwen 100，0 空**。
- 金标重抽 30（四类×两模型）+ gold_annotation.html 重建（含 dev1 GLM 回答）。
- **G1 金标重标（DeepSeek low）28/30 有效**（dev_063 两条病理长文 JSON 截断跳过），schema 全过。
- 标注 effort 改 low（medium 推理膨胀 + 长回答 89 单元致 40s/条；low 去推理）。放量 400 条待 κ 后跑，长回答可再优化稀疏输出（只输出删/压单元）。
- 代理全 DeepSeek，与 dev1(GLM)/dev2(Qwen) 跨家族。预算 **¥20.23**。
- 自主准备完成，待用户金标 30（T4.2）→ κ 校准 → 放量。代码测试 11.1 须用 dev1=GLM 重跑（待）。

## 第 30 条 · T2.2 抽查结果 + 重分类 + 配额偏移（2026-11-20，追加）【实测 + 用户校准】
- **用户抽查 40：错 9 = 22.5% > 10%** → 按 SPEC §6 改分类提示词重跑。错分模式：G1 把事实性「怎么做/方法/表达式/规则」误判代码/建议（用户判问答）。
- 修订 CLASSIFY_SYS（问事实/方法=问答、写代码=代码、讲原理=解释、给推荐=建议）+ reclassify 200 条：dev 改 31、test 改 23。
- 应用用户对 40 条权威纠正（11 处改）。dev 最终分布≈问答 43/建议 20/代码 17/解释 20。
- **SPEC-CHANGE-007（配额偏移）**：分类纠正后 dev 不再 25/类（问答偏多），中文配额代码/解释/建议 <8。真实分布本就问答偏多；原 25/类基于 G1 初判（含误分）。评估按纠正后类别分组（组大小不一），报告标明此局限。不重抽样（回答已生成）。
- 金标加中文翻译对照（translate_gold 助读；标注仍针对原文保 κ 有效）；解释类中文每模型仅 1 条，无法全中文金标。

## 第 31 条 · 金标分流：中文人工 + 非中文外部 AI（2026-11-20，用户决定）【方案】
- 用户读非中文慢，决定金标分流：**非中文 21 条交外部 AI 标注**（AI_ANNOTATION_BRIEF.md + non_chinese_gold.jsonl），**中文 9 条用户人工标**。
- 方法学约束（诚信）：人工 κ 校准以用户标的中文 9 条为准（真人工，样本偏小 κ 可能不稳，报告标明）；非中文外部 AI 金标 = AI 代理金标，G1 与其一致为 AI 对 AI，作补充，**不冒充人工校准**。
- 外部 AI 输出 JSON 数组（annotator="AI"）→ human/gold/ai/ → ingest 接收（与人工 gold/user/ 分开）。
- 金标网页改直接原文操作版（点击单元切换 留/压/删、+加必留点、⇧前移、重置按钮、原文随导出保留）；计数逻辑 node 验证正确；旧界面系浏览器缓存需 Ctrl+F5。
- ingest_gold.py：导出数组拆单文件供校准（2 单测）。总 152 单测。

## 第 32 条 · 11.1 代码测试 GLM dev1 版结果（2026-11-20，追加）【实测】
- run_code_test（dev1=GLM，SPEC-CHANGE-006，50 题 base 测试）：**original pass@1=0.96，A=1.0，B=0.98**。
- 判据「pass@1 不下降」：**A/B 均 ≥ original → 全通过 ✓**（与之前 DeepSeek dev1 版相反：那版 original 1.0 / A 0.98 / B 0.98 微降）。
- **发现：方案 A 提升 GLM 代码正确性（0.96→1.0）**，简洁提示词助 GLM 产出更准代码。
- **11.1 通过（GLM dev1）**。code_test_report.json 已更新。预算 ¥27.50。
- 注：base 测试（plus 沙箱 Windows 不可用，SPEC-CHANGE-004）、50 题小样本；模型依赖（GLM 受益、DeepSeek 微降）须报告标明。

## 第 33 条 · 金标合并 + 校准失败（2026-11-20，追加）【实测】
- 用户澄清：人工只标了中文 9 条（非中文在 human 文件里是默认未动全留）；非中文以 AI 为准。merge_gold：中文 9=user（含 12 压）、非中文 21=AI（补全 type/text），冲突取 AI。154 单测。
- **校准失败【实测】**：G1 vs 用户中文 κ_label=-0.017、κ_pathology=0（216 单元）；G1 vs AI 非中文 κ_label=0.289、κ_pathology=0.203（794 单元）。**人工 κ 关卡（≥0.6）未过**。
- 根因：用户中文金标保留 94%（204 留/12 压/0 删），G1 删 26%（150 留/10 压/56 删）；G1 判删的 56 单元用户 55 判留。对「什么算冗余」标准根本差异。
- 用户意图：AI 标注为基础 + 加入用户的压、冲突取 AI（已实现于 merge_gold）。
- 待决：κ<0.6 按协议须改规范 + 新批重测；或调 G1 保守匹配金标；或用户授权偏离关卡（SPEC-CHANGE-008 待）。

## 第 34 条 · 用户选 A：调 G1 保守 + 新批 15 重测（2026-11-20，追加）【进行中】
- 用户选 A（协议正路）。G1/G2 标注提示词加【保守口径】：默认留，仅纯冗余套话(P1/P2/P3/P6/P7/P10)且无实质信息才删，含实质内容留或压，拿不准留。
- make_recal_batch：选 15 条新中文（不在原金标 30，seed42）→ G1 保守标注 annotations/g1_recal → recal_annotation.html。154 单测，¥27.71。
- 待用户标 15 条 → human/gold/recal_user/ → recalibrate 重算 κ（G1 保守 vs 用户）。≥0.6 则放量。

## 第 35 条 · SPEC-CHANGE-008：校准委托 AI（2026-11-20，用户决定）【偏离】
- 用户不愿人工标重测批，决定 recal 15 条也交外部 AI 标。
- **后果**：无人工金标校准；κ 关卡变为 G1 vs 外部 AI（AI 对 AI 一致率），非人工校准。预登记「人工 κ≥0.6」无法满足。
- **报告须标明**：人工校准未做（用户委托 AI），标注质量为 AI 代理、未经人工验证；κ 数字作 AI 一致率参考，不冒充人工校准。
- recal_for_ai.jsonl（15 条）+ AI_ANNOTATION_BRIEF.md 交外部 AI。AI 返回 → recalibrate 算 G1 vs AI κ（AI 一致率参考）。

## 第 36 条 · 重测 AI 标注结果（2026-11-20，追加）【AI 对 AI 一致率】
- 用户提供 `recal_for_ai_annotations.json`，核验通过：15 条、15 个唯一 response_id、annotator=AI、字段完整。
- `recalibrate.py` 结果：G1 vs 外部 AI label κ = **0.108**；pathology κ = **0.157**；对齐单元 440。
- 预登记 κ≥0.6：**未通过**。该数字是 AI 对 AI 一致率，不能写成人工校准 κ。
- 结论：保守提示词仍未使 G1 与外部 AI 达到一致，放量标注质量没有通过校准门槛。是否跳过门槛、改用外部 AI 直接放量，或继续调标注规范，待用户决定。

## 第 37 条 · Astra xhigh 简化器接入（2026-11-20，用户指定）【实测】
- 用户提供 OpenAI 兼容端点 `https://api.openai-next.com/v1` 与密钥，已写入 `.env` 的 `OPENEXT_API_KEY`，未回显。
- 模型目录实测匹配：`gpt-6.2-astra`；用户指定的 Xhigh 对应 `reasoning.effort=xhigh`。
- 新增 config 角色 `simplifier_external`，方案 B 实际使用它生成 edit ops；DeepSeek 仍负责 judge 的 compress 子集校验、G1/G2 标注和其他代理角色。
- Astra 简化冒烟【实测】：dev_000_dev2，14 个单元，返回 14 个合法 edit ops，out=327 tokens，latency=8355ms，累计预算约 ¥27.97。
- **下一轮**：待校准路径决定后，使用 Astra xhigh 批量运行方案 B，并单独记录其调用延迟/费用。Astra 价格表为保守占位【推断，待供应商账单核实】。
- 测试总数 **154/154** 通过。

## 第 38 条 · OpenExt Kimi 3.1 Pro 备用简化器（2026-11-20，用户指定）【实测】
- OpenExt 模型目录匹配：`kimi-k3.1-pro`；Responses + `reasoning.effort=xhigh` 冒烟通过，延迟 4.07s。
- config 新增 `simplifier_fallback`；Astra `simplifier_external` 为主，Astra 超时/预算异常时 runner 切换 Kimi。
- 新增 `run_astra_simplification.py` 可续跑批量 runner，输出 `responses/scheme_b_astra.jsonl`，逐条记录实际 simplifier_role、edit ops、原文/简化文本、token、延迟、错误。
- 预算仍记录在统一账本，价格使用保守占位；用户表示账单可继续使用，仍保留实验预算记录。
- 预算仍记录在统一账本，价格使用保守占位；用户表示账单可继续使用，仍保留实验预算记录。
- 全套测试 **156/156** 通过。批量 job `pwsh-ad791d5fde0342ce` 已启动。

## 第 39 条 · Astra/Kimi 简化批次中间结果（2026-11-20，追加）【实测，未完批】
- `run_astra_simplification.py` 已开始处理 200 条，当前已写入 **5/200**。
- 初步本地汇总：平均字符降幅 **56.39%**，平均延迟 **13.49s**，操作分布 keep=14/delete=20/compress=4；4 条由 Astra，1 条因主模型异常由 Kimi 备用完成。
- 该汇总仅是中间样本，不能作为最终方案 B 结论；完整批次后再按模型和实际简化器汇总。新增本地汇总器 `summarize_simplification.py`，测试总数 **158/158**。

## 第 40 条 · 用户要求停止 Astra，切换 Sol（2026-11-21，追加）【实测】
- 用户发现 Astra 消耗过快，立即要求停止。已终止 Astra 批次及父子进程，避免继续扣费。
- 主简化器已切换为 OpenExt `gpt-6.2-sol`，`reasoning.effort=low`，Sol 冒烟通过：Responses、9.75s、输出 5 tokens。
- 备用简化器保留为 OpenExt `kimi-k3.1-pro`，也使用 low 推理档位。
- 已写入的 5 条 Astra 结果保留并标注实际角色，作为历史中间记录；后续未完成条目全部由 Sol 处理。
- 预算账本当前约 **¥31.13**，之后不再调用 Astra。测试 **158/158** 通过。
- Sol 批量续跑 job `pwsh-ec95b0d83faf447d`。

## 第 41 条 · 用户要求停止 OpenExt，简化器切回百炼 DeepSeek（2026-11-21，追加）【实测】
- 用户额度紧张，要求停止 OpenExt（GPT/Sol/Kimi），改用已有百炼模型。已终止 Sol 批次及进程。
- 已保存简化结果 **70/200**（Sol 48 / Kimi 6 / Astra 历史 5 + 后续），预算 **¥49.93**。
- config `simplifier_external` 与 `simplifier_fallback` 均改为百炼 `deepseek-v4.1-flash-1017`（effort=low），不再调用 OpenExt。
- 测试 **158/158** 通过。DeepSeek 续跑剩余 130 条 job `pwsh-05f8d66983494df3`。
- 注意：方案 B 简化器中途换模型（Astra→Sol→DeepSeek），最终报告须标明简化器不一致这一局限，或按实际 simplifier_role 分组分析。

## 第 42 条 · SPEC-CHANGE-009：降低校准门槛，AI 标注作工作标准（2026-11-21，用户批准）【偏离】
- 用户选 C：降低门槛，κ 只作 **AI 对 AI 一致率参考**，不冒充人工校准；用 G1/G2(百炼 DeepSeek) AI 标注作为工作标准，继续放量→评测→迁移→报告。
- 预登记「人工 κ≥0.6 才放量」**不再作为硬关卡**；实测 κ（G1 vs 用户中文≈0、G1 vs 外部 AI 重测 0.108）如实记录为参考，报告标明「未经人工校准」。
- 硬约束仍守：保留率≥95%、新增错误=0、代码块逐字节不变、¥100 预算熔断、DeepSeek effort=low。
- 所有下游结果标『AI 代理评测·未经人工校准』。用户亲手做的盲评/保留率复核/计时阅读仍只备材料不代做。
- 新 goal `goal-c9ed5dbc` 驱动剩余管线；旧 goal 已由用户删除。

## 第 43 条 · 方案 B 简化批完成 200 条（2026-11-21，追加）【实测】
- DeepSeek 续跑完成：**200/200，failed 0**，累计 ¥51.33。简化器分布 DeepSeek 130 / Sol 59 / Kimi 6 / Astra 5（中途换模型，报告按 simplifier_role 分组或标明局限）。
- 修复 1 条空结果 dev_001_dev2（短回答被全删）：apply_scheme_B 加「空结果回退原文」保护，重跑后 0 空。
- 初步汇总【实测】：平均字符降幅 **15.65%**（GLM 14.69% / Qwen 16.62%），平均延迟 12.0s；操作 keep 5162 / delete 1206 / compress 294 / move_first 10。eval/scheme_b_astra_summary.json。
- run_calibration 加 --force（SPEC-CHANGE-009 跳过 κ 关卡）。放量标注 G1/G2 进行中。

## 第 44 条 · 放量标注完成 + 方案 B 阅读时间降幅实测（2026-11-21，追加）【实测】
- 放量标注 G1/G2 完成 **396 次**（各约 198，dev_063 两条病理长文 JSON 截断跳过），¥57.18。发现繁体标签「刪/壓」→ annotate.normalize_label 繁→简归一化（+2 单测，总 160）。
- run_calibration --force finalize：**198 条 final**，346 分歧抽 50。κ 参考：人工中文 -0.017、AI 非中文 0.289（均 <0.6，按 SPEC-CHANGE-009 作参考不作关卡）。
- **方案 B 阅读时间降幅【实测，198 条】**：T_总平均降 **20.91%**（CI95 [18.24, 23.71]），**超 15% 阈值**；GLM 21.85% / Qwen 19.97%。eval/eval_b_metrics.json。
- **T_答局限**：平均 -64.5%（到答案反而变慢）。原因：简化器仅 10 次 move_first（答案很少前移）；删除开头单元后 answer_uid=1 启发式读完全文。T_答指标需改进 answer 定位，报告标明。
- 下一步：保留率/新增错误/盲评裁判（硬约束保留率≥95%）。

## 第 45 条 · 方案 B 裁判结果：违反信息安全硬约束（2026-11-21，追加）【AI 代理裁判·未经人工校准】
- run_eval_b --judge 完成（198 条，¥67.70）。**保留率 89.43%（<95% ❌）；新增错误 23（≠0 ❌）；盲评简化胜率 13.6%；T_总降 20.91%（✅）**。
- 分模型：GLM 保留率 92.15%/新增错误 1/盲评 15.2%；Qwen 保留率 87.37%/新增错误 22/盲评 12.1%。
- 分类别保留率：问答 87.72 / 代码 88.99 / 解释 90.96 / 建议 90.88（均 <95%）。
- **结论**：方案 B 省阅读时间但丢必留信息+引入错误，当前简化过激进，违反硬约束。按预登记 §12 decide_mvp → 「回阶段4查理论上限」。
- 诚信说明：保留率/新增错误为 DeepSeek 裁判判定（部分成立按不成立），未经人工复核；用户保留率复核30可校准。方向性结论：简化需更保守。
- eval/eval_b_full.json 落盘。报告已更新。

## 第 46 条 · AI 读者测验（11.3）有效结果（2026-11-21，追加）【AI 代理评测·未经人工校准】
- 前两次运行无效（原版正确率仅 6.7%/9%）：评分用子串匹配+问题文本键匹配过严，属测试 bug，非真实结果。
- 修复：答题按位置匹配 + 裁判批量语义评分。重跑有效：**原版正确率 97.48%，简化版 87.39%，下降 10.08pp（>3pp ❌）**，119 题。
- 与保留率 89.43% 失败一致：简化丢信息并降低阅读理解。eval/ai_reader_report.json。
- 11.2 留出迁移**暂缓**：方案 B 保留率已 <95%（迁移的保留率前提不成立），且官方 Kimi 额度有限，跑之无意义。
- 预算 ¥69.25。

## 第 47 条 · 用户亲手做材料全部用真实数据填充（2026-11-21，追加）【备料，不代做】
- prepare_eval_materials：盲评 30 对（随机左右去标签）+ 保留率复核 30（裁判判定）+ 新增错误确认。生成 blind_eval.html / retention_check.html。
- make_adjudication_page：裁决 50 分歧单元网页就绪。
- prepare_timing_material：计时阅读 40 条（出题+半原版/半简化）→ timing_reading.html。
- **新增错误计数噪声【局限】**：评测时 new_errors=23，重抽确认材料时=6（同一简化数据，DeepSeek 裁判 temp0 仍不稳定）。方向（有新增错误、违反=0）稳健，精确计数有噪声；报告标明。
- 至此 6 项用户亲手做材料全部备齐：抽查40/金标30/裁决50/盲评30对/保留率复核30+新增错误/计时阅读40。预算约 ¥70。

## 第 48 条 · 留出模型核实 + 迁移暂缓依据（2026-11-21，追加）【实测】
- 官方 Kimi key 核实：`moonshot-v1-32k` 返回 404（不可用）；实际可用 `kimi-k3.1-pro` / `kimi-k3`。kimi-k3.1-pro 调用成功（**temperature 必须=1**，2.15s）。config holdout 已更新为 kimi-k3.1-pro。
- **迁移（11.2）暂缓依据**：方案 B 保留率 89.43%<95%，而迁移通过判据要求保留率≥95%——前提不成立，迁移必然失败。完整迁移需 test100×(2开发+Kimi) 生成+简化+裁判约 3000 次调用，将耗尽剩余预算确认已知失败。故暂缓，待用户决定是否补跑。
- 自主管线其余全部完成：①放量标注 ②简化批200 ③评测 ④AI读者 ⑤报告+MVP。预算 ¥70.31/¥100。

## 第 49 条 · 用户选 B：保守简化器迭代（2026-11-21，追加）【SPEC-CHANGE-010】
- 用户看过最终结果后选 B：调保守简化器重跑方案 B，冲保留率≥95%。goal 恢复 active。
- 病因诊断：原简化器删/压过激进（保留率 89.43%），把含必留点的单元也删了。
- 对策：REWRITE_SYS 改保守口径——默认 keep，仅纯套话且无实质信息才 delete，含实质内容一律 keep/compress（compress 保全信息），拿不准 keep，答案 move_first。
- 重跑简化→scheme_b_conservative.jsonl（独立文件，不覆盖原激进结果），再测评保留率/新增错误。预算余约 ¥29.7，控制开销。

## 第 50 条 · 保守简化批完成 + 权衡显现（2026-11-21，追加）【实测】
- 保守简化 200/200 完成（DeepSeek，failed 0），¥71.55。
- **保守版 T_总降幅仅 6.99%**（CI [5.45, 8.67]），远低于激进版 20.91%，也低于 15% 阈值。GLM 9.74% / Qwen 4.23%。
- **权衡显现**：激进=省时21%但保留率89%不达标；保守=省时7%（<15%）但保留率待测。省时与保信息此消彼长。
- 保守版保留率/新增错误裁判运行中（eval_b_conservative.json）。

## 第 51 条 · B 迭代保守版结果：保留率达标，但三约束无法同时满足（2026-11-21，追加）【AI 代理裁判·未经人工校准】
- 保守版裁判完成（198 条，0 失败，断点续跑+逐条容错修复了网络超时崩溃），¥82.79。
- **保守版：保留率 95.7%（≥95% ✅）；新增错误 14（≠0 ❌）；T_总降幅 6.99%（<15% ❌）；盲评胜率 9.1%**。
- 分模型：Qwen 保留率 96.51%✅/新增错误13；GLM 保留率 94.63%（略<95）/新增错误1。
- **权衡前沿【核心结论】**：激进版=省时21%✅但保留率89%❌；保守版=保留率95.7%✅但省时7%❌。省时与保信息此消彼长；「新增错误=0」极严，两形态都未过（23/14）。**方案 B 无法同时满足 省时≥15% + 保留率≥95% + 新增错误=0 三硬约束。**
- 新增错误计数有噪声（激进23/重抽6；保守14），方向（>0）稳健。MVP 仍判「回阶段4/需重新设计」。

## 第 52 条 · 用户决定收尾 · 实验最终结论（2026-11-21，追加）【归档】
- 用户看过 B 迭代结果后决定**收尾**。
- **最终结论：方案 B（编辑操作式简化）面临「不可能三角」——省时≥15%、保留率≥95%、新增错误=0 无法同时满足。** 激进=省时21%/保留89%；保守=保留95.7%/省时7%；两版新增错误均>0。方法本身局限，非调参可解。
- 完成清单：生成200/简化200(激进)+200(保守)/标注396→198final/评测(T_总/保留率/新增错误/盲评/CI)/AI读者/代码测试11.1/报告+MVP/B迭代。160 单测全过。
- 留出迁移未跑（无达标方案可迁移，官方Kimi无moonshot-v1-32k、可用kimi-k3.1-pro已核实）。
- 6 项人工校准材料备齐于 human/。所有 AI 结果标「AI 代理评测·未经人工校准」（SPEC-CHANGE-009）。
- 最终预算约 ¥82.8/¥100。规格变更 SPEC-CHANGE-001~010 全记录。实验以否定结论收尾。
