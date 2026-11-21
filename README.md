# LLM 输出精简工具（LLM Output Simplifier）

把啰嗦的 LLM 输出/文本精简成更短的版本：切分单元 → LLM 生成编辑操作（删/压/前移）→ 确定性重组。
以 **MCP 工具**形式提供，Claude / DSH / 任何 MCP 兼容 Agent 都能直接调用。

> ⚠️ **重要限制（实验实测）**：精简会丢信息、可能引入错误。详见下方「实验结论」。
> **精简重要内容（医疗/法律/代码/关键数据）后务必人工核对。** 它最适合删明确的套话，不适合精简信息密集内容。

---

## 快速开始（MCP，推荐）

### 1. 安装
```powershell
cd llm-output-simplifier
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
Copy-Item .env.example .env   # 填入 DASHSCOPE_API_KEY（百炼，简化器用 DeepSeek）
```

### 2. 接入你的 Agent
把下面加到 Agent 的 MCP 配置（如 Claude Desktop 的 `claude_desktop_config.json`，或 DSH 的 MCP 设置）。
把路径换成你的实际项目路径：

```json
{
  "mcpServers": {
    "llm-simplifier": {
      "command": "C:\\path\\to\\llm-output-simplifier\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\llm-output-simplifier\\scripts\\mcp_server.py"]
    }
  }
}
```

重启 Agent，即可调用两个工具：
- **`simplify(text)`** → 返回精简后的文本
- **`simplify_with_stats(text)`** → 返回精简文本 + 降幅/操作统计

### 3. 示例
输入：
> 当然可以！这是一个非常好的问题，我很乐意帮你解答。下面我将详细介绍…答案是 42…总而言之综上所述…希望对你有帮助！

输出：
> 这个问题的答案是 42。

（删掉开场白/结尾客套/重复总结，答案前移。）

---

## 命令行用法（给有 shell 权限的 Agent / 手动）

```powershell
.\.venv\Scripts\python.exe -m scripts.simplify_text --text "要精简的文本"
.\.venv\Scripts\python.exe -m scripts.simplify_text --input 输入.txt --out 精简.txt
```

---

## 工作原理（方案 B）

1. **切分**（`scripts/segment.py`）：把文本切成单元（句/列表项/表格行/整块代码）。代码块逐字节保留。
2. **编辑操作**（`schemes/scheme_b_rewrite.py`）：LLM（百炼 DeepSeek）对每个单元输出 `delete / keep / compress / move_first`，只输出操作、不自由重写。`compress` 经裁判做「信息子集」校验，失败回退 keep。
3. **确定性重组**（`schemes/scheme_b.py`）：按操作重组，代码块只整块 keep/delete，`move_first` 最多一次，空结果回退原文。

当前为**保守口径**：默认保留，仅纯套话（复述开场/AI 免责/路标句/空洞收尾/说教/结尾复述）且无实质信息才删。

---

## 实验结论（为什么有上面的限制）

在 200 条真实 LLM 回答上做了预登记实验（AI 代理评测，未经人工校准），发现**「不可能三角」**：

| | 省时≥15% | 保留率≥95% | 新增错误=0 |
|---|---|---|---|
| 激进简化 | ✅ 21% | ❌ 89% | ❌ 23 |
| 保守简化 | ❌ 7% | ✅ 95.7% | ❌ 14 |

**省时与保信息此消彼长，「零错误」极严——编辑操作式简化无法同时满足三者。** 这是方法本身的局限，不是调参能解决的。
完整报告见 [`reports/final_report.md`](reports/final_report.md)，方法规格见 [`SPEC.md`](SPEC.md)，实验日志见 [`logs/experiment_log.md`](logs/experiment_log.md)。

---

## 配置说明

- 简化器模型在 `config.yaml` 的 `models.simplifier_external`（当前：百炼 `deepseek-v4.1-flash-1017`，`reasoning.effort=low`）。
- 密钥只放 `.env`（已被 `.gitignore` 排除），`config.yaml` 只引用环境变量名。
- 预算熔断：`config.yaml` `budget.cap_cny`（默认 ¥100）。

## 项目结构

```
scripts/     MCP 服务、CLI、抽样/生成/标注/评测/报告等管线脚本
schemes/     方案 A/B/C/F 实现
eval/        阅读时间指标、裁判、统计、聚合
tests/       单元测试（160 项）
reports/     最终报告
SPEC.md      实验规格（预登记）
RUNNING.md   完整实验管线运行说明
```

## 复现实验
完整管线（抽样→生成→标注→评测→报告）见 [`RUNNING.md`](RUNNING.md)。注：实验数据文件（responses/annotations 等）未纳入本仓库，需按 RUNNING.md 重新生成。

## 许可
本项目为实验性工具，使用请自行评估风险，精简结果务必人工核对。
