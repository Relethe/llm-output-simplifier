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

### 3. 示例（来自真实实验数据，非虚构）

以下取自 200 条真实 LLM 回答实验（提问来自 LMSYS 真实用户对话，回答由 GLM/Qwen 生成）。

**例 1 · 事实问答（Qwen，降 81%）**
提问：鲁迅和周树人是什么关系？

原文（326 字，含本名/笔名由来/家人/网络段子等大量展开）：
> **他们是同一个人**——鲁迅是笔名，周树人是本名。
> - **本名**：周树人，字豫才，1881 年生于浙江绍兴，1936 年病逝于上海。
> - **笔名由来**：1918 年在《新青年》发表《狂人日记》时首次署名"鲁迅"……他一生用过一百多个笔名。
> - **家人**：二弟周作人、三弟周建人……
> 所以问"鲁迅和周树人什么关系"，就像问"马克·吐温和塞缪尔·克莱门斯什么关系"……

精简（61 字）：
> **他们是同一个人**——鲁迅是笔名，周树人是本名。1918 年，他在《新青年》发表《狂人日记》时，首次署名"鲁迅"。

⚠️ 注意：此例删掉了生卒年、家人、笔名典故等**实质细节**——核心答案保住了，但展开信息丢了。这正是「会丢信息」的实例，重要内容需人工核对。

**例 2 · 代码（GLM，降 57%，代码块逐字节保留）**
提问：给 students/departments 表，写 SQL 查计算机系学生。

精简后（两个 SQL 代码块原样保留，只压缩了文字解释）：
> ```sql
> SELECT s.id, s.sn
> FROM students s
> JOIN departments d ON s.did = d.id
> WHERE d.dn = 'Computer Science';
> ```
> Joins on department id and filters by department name.

> 规律：**套话多的回答降幅大，信息密集的回答降幅小**；代码块始终整块保留。真实优质回答本就干净，可精简空间有限（详见实验结论）。

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

## 如何更换 API / 模型（换服务商必看）

简化器走 **OpenAI 兼容接口**，所以任何提供 OpenAI 兼容端点的服务商都能接。改 `config.yaml` 里 `models.simplifier_external` 的 4 个字段即可：

```yaml
simplifier_external:
  model: deepseek-v4.1-flash-1017        # ① 模型 ID
  base_url: https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1  # ② API 端点
  api_key_env: DASHSCOPE_API_KEY         # ③ 密钥对应的环境变量名
  api_protocol: responses                # ④ 协议：responses 或 chat
  default_reasoning_effort: low
```

**步骤：**
1. 改上面 4 个字段为你的服务商值。
2. 在 `.env` 里加上 ③ 指定的环境变量和密钥，例如 `OPENAI_API_KEY=sk-...`。
3. 跑冒烟测试验证：`.venv\Scripts\python.exe -m scripts.smoke_test`。

**常见服务商示例：**

| 服务商 | base_url | api_protocol | 备注 |
|---|---|---|---|
| 阿里云百炼（默认）| `https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1` | `responses` | 用 `DASHSCOPE_API_KEY` |
| OpenAI 官方 | `https://api.openai.com/v1` | `responses` | 用 `OPENAI_API_KEY` |
| DeepSeek 官方 | `https://api.deepseek.com/v1` | `chat` | 用 `DEEPSEEK_API_KEY` |
| Moonshot Kimi | `https://api.moonshot.cn/v1` | `chat` | 用 `MOONSHOT_API_KEY`，部分模型仅允许 `temperature=1` |
| 其他兼容端点 | 服务商提供的 `/v1` 地址 | 视支持情况 | 先确认支持 responses 还是 chat |

**两个常见坑：**
- **协议不匹配**：不是所有端点都支持 Responses API。若报接口错误，把 `api_protocol` 改成 `chat` 再试。
- **参数限制**：有的模型限制 `temperature` / `reasoning` 参数（如 kimi-k3.1-pro 只允许 `temperature=1`）。换模型后务必先跑 `smoke_test` 验证。

> 备用简化器 `models.simplifier_fallback` 同理可改；主简化器超时/异常时会自动切到它。

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
