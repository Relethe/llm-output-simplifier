"""通用 LLM 输出精简工具 · MCP 服务。
把精简能力暴露为 MCP 工具，供 Claude / DSH / 任何 MCP 兼容 Agent 调用。
启动（stdio）：.venv\\Scripts\\python.exe -m scripts.mcp_server
工具：simplify(text) / simplify_with_stats(text)
注意：实验表明精简可能丢信息/引入错误（保留率最高95.7%），重要内容需人工核对。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))
from mcp.server.fastmcp import FastMCP  # noqa: E402
from scripts.llm_client import LLMClient, load_config  # noqa: E402
from scripts.segment import segment  # noqa: E402
from schemes.scheme_b_rewrite import apply_scheme_B  # noqa: E402

mcp = FastMCP("llm-output-simplifier")
_client = None


def get_client():
    global _client
    if _client is None:
        _client = LLMClient(load_config(os.path.join(ROOT, "config.yaml")), phase="dev")
    return _client


@mcp.tool()
def simplify(text: str) -> str:
    """精简一段文本/LLM 输出：切分单元→LLM 编辑操作（删/压/前移）→确定性重组，保守口径。
    返回精简后的文本。注意：可能丢失部分信息或引入错误，重要内容请人工核对。"""
    if not text or not text.strip():
        return text
    units = segment(text)
    result = apply_scheme_B(get_client(), units, return_details=True)
    return result["text"]


@mcp.tool()
def simplify_with_stats(text: str) -> dict:
    """精简文本并返回统计：精简文本、原文/精简字符数、降幅百分比、编辑操作分布、单元数。"""
    if not text or not text.strip():
        return {"simplified": text, "reduction_pct": 0.0, "original_chars": len(text or ""),
                "simplified_chars": len(text or ""), "ops": {}, "units": 0}
    units = segment(text)
    result = apply_scheme_B(get_client(), units, return_details=True)
    simp = result["text"]
    ops = {}
    for op in result["ops"]:
        ops[op.get("op")] = ops.get(op.get("op"), 0) + 1
    return {"simplified": simp, "original_chars": len(text), "simplified_chars": len(simp),
            "reduction_pct": round((len(text) - len(simp)) / max(len(text), 1) * 100, 2),
            "ops": ops, "units": len(units),
            "caveat": "精简可能丢信息/引入错误，重要内容请人工核对"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
