# 实验日志 experiment_log.md

> 本文件在实验开始前预注册决策规则与规格变更。每条结论标明【实测】或【推断】。
> 规格 of record：`SPEC.md`。工单与依赖：`TICKETS.md`。

## 2026-11-19 预注册（实验开始前，阶段 0）

### 随机种子
42。所有抽样、bootstrap 重采样、盲评左右顺序随机均用此种子。

### 模型阵容（Path 2，四家）
| 角色 | 家族 | 模型 ID（默认，版本待冒烟确认） | base_url | key 环境变量 |
|---|---|---|---|---|
| 开发 1 | deepseek | deepseek-chat | https://api.deepseek.com/v1 | DEEPSEEK_API_KEY |
| 开发 2 | qwen | qwen-plus | https://dashscope.aliyuncs.com/compatible-mode/v1 | DASHSCOPE_API_KEY |
| 改写(B) | qwen | qwen2.5-7b-instruct | 同 DashScope | DASHSCOPE_API_KEY |
| 裁判 | glm | glm-4-flash（免费） | https://open.bigmodel.cn/api/paas/v4 | GLM_API_KEY |
| 留出 | kimi | moonshot-v1-8k | https://api.moonshot.cn/v1 | MOONSHOT_API_KEY |

家族约束校验【推断，基于公开家族归属】：裁判 GLM ∉ 开发{DeepSeek,Qwen} ∪ 改写{Qwen} ✓；留出 Kimi ∉ 开发 ∪ 裁判 ✓。
留出模型 `dev_phase_locked: true`，开发期间（阶段 0–6）一律不调用，仅阶段 7 迁移测试启用。

### SPEC-CHANGE-001（用户批准，2026-11-19）
- **变更**：开发模型由「3 个不同家族」改为「2 个家族」（DeepSeek, Qwen）。
- **原因**：用户仅有 DeepSeek/Qwen 额度 + 少量 Kimi + 免费 GLM；四家无法同时满足「3 开发家族 + 独立裁判 + 留出」且 Kimi 额度不足以承担高频角色。经 ask_user_question 确认，用户选择 Path 2。
- **连带调整**：
  - 阶段 0 验收：「2 个模型各跑通 1 条请求」（原 3）。
  - 阶段 3：responses_dev = 100 提问 × 2 模型 = **200 条**（原 300）。
  - 阶段 4：双人标注 **200 条**（原 300）；标注工作量相应下降。
  - 阶段 6：按 **2 个模型** × 4 类别报告（原 3 模型）。
  - 阶段 7：测试集回答用 **2 开发 + 1 留出（Kimi）= 3 模型**（原 4）。
  - 迁移判据不变：留出(Kimi) T_总降幅 ≥ 开发(2 家)平均值的 70%，保留率 ≥ 95%。
- **局限（最终报告须标明）**：跨家族泛化证据由 3 家减为 2 家；开发模型间的病症分布对比少一个数据点。

### 决策规则（预注册，源自 SPEC.md §11；阈值为建议起点，用户可调）
1. 若方案 A 的 T_总 比基线再降 **≥ 15%**，且保留率 **≥ 95%**、新增错误数 **≤ 基线** → **MVP = F + A**。
2. 否则若方案 B 满足上述条件 → **MVP = F + B**。
3. 两者都不满足 → 回阶段 4 检查理论上限（确认原始回答是否真啰嗦）。
- 基线 = 系统提示词仅「请简洁回答。」，位置与 A 相同。
- 主指标 T_总 = Σ(L_i / v_类型(i)) + c·N_结构；v/c 由阶段 1 标定（英文初始 238 wpm 仅参考，中文/代码/表格必须标定）。
- 硬约束：必留信息保留率 ≥ 95%；新增错误 = 0；代码块逐字节不变。

### 外部验证通过标准（预注册，源自 SPEC.md §10）
- 读者测验：正确率下降 ≤ 3 个百分点；实际阅读时间下降 ≥ 30%。
- 代码测试：EvalPlus pass@1 不下降。
- 迁移测试：见 SPEC-CHANGE-001。

### 裁判质量备注【推断】
glm-4-flash 为免费轻量模型，判保留率/新增错误精度弱于旗舰；以 SPEC §9.2 人工复核 10% 兜底。若 GLM 有付费额度可升级 glm-4-plus 提精度（待用户确认）。

---

## 环境记录（2026-11-19，T0.1）【实测】
- 系统：Python 3.14.6 / pip 26.2.1 / git 2.55.0 / uv 0.13.6（均在 PATH）。
- 项目 venv：uv 管理的 **CPython 3.12.16**（`.venv/`）。选 3.12 而非系统 3.14，因 3.14 过新、部分科学计算包 wheel 不全【推断动机，3.12 安装成功为实测】。
- 依赖版本（`importlib.metadata` 实测，全部 import 成功）：openai 3.55.1 / litellm 1.110.0 / pandas 3.1.1 / numpy 2.5.5 / scipy 1.18.1 / scikit-learn 1.9.1 / pysbd 0.3.4 / datasets 5.2.0 / pyyaml 6.0.3 / python-dotenv 1.2.4。
- config.yaml 解析实测：seed=42，dev_n=2，judge=glm-4-flash，holdout.dev_phase_locked=True。
- **环境观察 1（SSL）**：litellm 启动拉取 GitHub raw 的 model cost map 报 `SSL: CERTIFICATE_VERIFY_FAILED`（unable to get local issuer certificate），自动回退本地备份。判断为本机网络对 GitHub raw 的 SSL 拦截/CA 缺失【推断】；不影响国内 API 端点（deepseek/dashscope/bigmodel/moonshot），但**冒烟测试(T0.2)需实测确认国内端点证书正常**。成本统计我方自行记录，不依赖该 cost map。
- **环境观察 2（pysbd）**：导入有 SyntaxWarning（invalid escape sequence），纯 Python 库老化所致，无害。
- **环境观察 3（PowerShell 退出码假象）**：uv/litellm 把进度与警告写 stderr，PowerShell `2>&1`/`2>$null` 会误报 NativeCommandError → exit code 1，**即便命令实质成功**。判定一律以输出实质为准，不凭 exit code（本会话已两次实证）。

## 实验运行记录
（每次模型调用批次、各阶段运行在此追加：日期、配置、结论【实测/推断】）

### 2026-11-19 T0.2 客户端 + 日志 + 熔断 + 留出锁【实测】
- 预算上限 **¥100**（用户批准），写入 config.budget.cap_cny，硬性熔断启用；价格表为近似值【推断·待官网核实】，熔断偏保守。
- 单元测试 **6/6 通过**（unittest，mock `_invoke`，零费用、不依赖密钥）：① 日志含 timestamp/role/model/model_version/params/tokens_in/out/latency_ms/cost/phase；② 预算达上限抛 BudgetExceededError 且不调 API；③ 留出模型开发期抛 HoldoutLockedError；④ 留出在 phase=test 可调用；⑤ 成本累计并持久化到 logs/budget_state.json、新客户端恢复；⑥ 真实 config.yaml 解析（seed42/cap100/dev_n2/holdout锁）。
- 实现：scripts/llm_client.py（统一 OpenAI 兼容客户端）；冒烟脚本 scripts/smoke_test.py 就绪。
- **冒烟通过【实测】（2026-11-19，阶段 0 验收达成）**：
  - 端点修正：百炼密钥属 **token-plan MaaS 端点** `https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`（非标准 dashscope 域名——首次 401 的根因）；API 协议 = **OpenAI Responses**（用户截图确认），客户端已支持 responses / chat 双协议。
  - 密钥来源：DSH `~/.dsh/.credentials.yaml` 的 `refs.ALI_API_KEY`（程序化写入 .env，未打印明文）；GLM_API_KEY 取自 `refs.ZHIPU_API_KEY` 备裁判用。
  - dev1 `deepseek-v4.1-flash-1017`：非空回答，in67/out43，1477.52ms，≈¥0.000239。
  - dev2 `qwen4-max`（用户口语「Qwen4」，实测 ID 确认）：非空回答，in69/out20，1456.3ms，≈¥0.00258。
  - 累计 ¥0.002819 / 上限 ¥100；logs/calls.jsonl 2 条字段齐全；端点证书正常（无 SSL 错误，环境观察 1 的待验项已确认）。
  - 单元测试 **7/7** 通过（新增 responses 协议解析测试）。
- **阶段 0 完成**。下一步阶段 1（标定网页 T1.1）/ 阶段 2（抽样 T2.1）——按用户指示暂停待命。
