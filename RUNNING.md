# 全流程运行说明（RUNNING）

> 规格 SPEC.md（v0.2）；预登记 + 规格变更 logs/experiment_log.md；工单 TICKETS.md。
> 环境：uv 管理 Python 3.12 venv（`.venv`）；密钥在 `.env`（勿提交）。所有命令在项目根目录跑。
> 证据纪律：AI 代理结果标「AI 代理评测（经 N 条人工校准）」，**不得写成人工评测**；【用户亲手做】步骤 AI 不代做。

## 0. 环境与冒烟
```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
uv pip install --python .venv\Scripts\python.exe evalplus   # 阶段7.1
Copy-Item .env.example .env   # 填 DASHSCOPE_API_KEY（百炼，含dev/GLM）/ MOONSHOT_API_KEY（Kimi留出）
.\.venv\Scripts\python.exe -m scripts.smoke_test
.\.venv\Scripts\python.exe -m unittest discover -s tests   # 144 单测
```
- 百炼端点 `token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`，**OpenAI Responses 协议 + 流式**。
- GLM 代理调用带 `reasoning.effort`（分类 low / 标注 medium）控开销；生成墙钟上限 240s + 空退避 medium（SPEC-CHANGE-003）。
- 留出 Kimi `dev_phase_locked`，开发期不调用。

## 1. 阅读速度参数
`reading_speed.json` 已建（英文 238 文献；中文/代码/表格/列表/c 占位·推断，待阶段 7.4 用户计时回归重算）。

## 2. 抽样（已完成）+ 用户抽查
```powershell
.\.venv\Scripts\python.exe -m scripts.sample_prompts   # dev/test 各100，每类25中文≥8
.\.venv\Scripts\python.exe -m scripts.make_spotcheck_page
```
**【用户亲手做 T2.2】** 打开 `human/classification_spotcheck.html` 判 40 条，错分 >10% → 改分类提示词重跑。

## 3. 生成原始回答
```powershell
.\.venv\Scripts\python.exe -m scripts.generate_responses   # 100×2模型=200，流式+墙钟+退避，可续跑
```

## 4. 标注与校准
```powershell
.\.venv\Scripts\python.exe -m scripts.make_gold_set        # 分层抽30金标候选
.\.venv\Scripts\python.exe -m scripts.make_gold_page       # 金标标注网页
```
**【用户亲手做 T4.2】** 打开 `human/gold/gold_annotation.html` 独立标 30 条 → 导出存 `human/gold/user/`。
```powershell
.\.venv\Scripts\python.exe -m scripts.run_annotation --mode gold --variants G1   # G1标金标
.\.venv\Scripts\python.exe -m scripts.run_calibration      # κ≥0.6放量；<0.6换新批15
.\.venv\Scripts\python.exe -m scripts.run_annotation --mode full --variants G1,G2  # 放量200（校准通过后）
.\.venv\Scripts\python.exe -m scripts.run_calibration      # 合并final+分歧清单抽50
.\.venv\Scripts\python.exe -m scripts.make_adjudication_page
```
**【用户亲手做 T4.5】** 打开 `human/adjudication/adjudication.html` 裁决 50 分歧单元。
```powershell
.\.venv\Scripts\python.exe -m scripts.make_pathology_report   # 病理统计+理论上限
```

## 5.1 Sol / Kimi 方案 B 简化
```powershell
.\.venv\Scripts\python.exe -m scripts.run_astra_simplification
```
主模型为 `gpt-6.2-sol`，`reasoning.effort=low`。请求超时或异常时切换 `kimi-k3.1-pro`。结果写入 `responses/scheme_b_astra.jsonl`，历史文件名保留以兼容已写入的 5 条记录，可中断后续跑。每条记录实际模型、edit ops、原文、简化文本、token 和延迟。

- A：`schemes/scheme_a.py`（13 规则 + 基线 + 消融）。
- B：`schemes/scheme_b.py` + `scheme_b_rewrite.py`（GLM 改写 + 确定性重组 + compress 子集校验）。
- C：`schemes/scheme_c.py`（logit_bias，百炼 Responses 不支持故 dev N/A）。
- F：`schemes/scheme_f.py` + `scheme_f_proxy.py` + `litellm_config.yaml`（需 litellm[proxy] 部署）。

## 6. 评测与消融
```powershell
.\.venv\Scripts\python.exe -m scripts.run_eval --conditions baseline,A,B,A+B   # 须final标注
.\.venv\Scripts\python.exe -m scripts.prepare_human_data   # 填充盲评/保留率/计时材料
.\.venv\Scripts\python.exe -m scripts.make_blind_eval_page
.\.venv\Scripts\python.exe -m scripts.make_retention_check_page
```
**【用户亲手做 T6.2】** `human/blind_eval/blind_eval.html` 判 30 对（一致率 ≥80% 采纳裁判盲评）。
**【用户亲手做 T6.3】** `human/retention_check/retention_check.html` 复核 30 保留率 + 确认全部新增错误。
消融：`eval/ablation.py`（A 去规则 1–11 / B 禁 op / F 去意图）。

## 7. 外部验证
```powershell
.\.venv\Scripts\python.exe -m scripts.run_evalplus --n 50 --conditions original,A,B   # 7.1代码测试（全自动）
.\.venv\Scripts\python.exe -m scripts.run_transfer       # 7.2迁移（须阶段7解锁Kimi+最优方案）
.\.venv\Scripts\python.exe -m scripts.ai_reader_test     # 7.3 AI读者测验（须final+40条）
.\.venv\Scripts\python.exe -m scripts.make_timing_page   # 7.4计时网页
```
**【用户亲手做 T7.4】** `human/timing/timing_reading.html` 计时阅读 40 条 → 回归阅读速度。

## 8. 结论与 MVP
```powershell
.\.venv\Scripts\python.exe -m scripts.make_report   # 按预登记§12决策规则装配final_report.md
```

## 用户亲手做 6 步汇总（约 5h）
| 步 | 网页 | 阶段 |
|---|---|---|
| 抽查 40 分类 | classification_spotcheck.html | 2 |
| 金标 30 | gold_annotation.html | 4 |
| 裁决 50 | adjudication.html | 4 |
| 盲评 30 对 | blind_eval.html | 6 |
| 保留率 30 + 新增错误 | retention_check.html | 6 |
| 计时阅读 40 | timing_reading.html | 7 |
