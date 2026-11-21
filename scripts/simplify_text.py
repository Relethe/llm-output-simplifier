"""通用 LLM 输出精简工具 · 单文本命令行入口。
用法：
  .venv\\Scripts\\python.exe -m scripts.simplify_text --text "要精简的文本"
  .venv\\Scripts\\python.exe -m scripts.simplify_text --input 输入.txt --out 精简.txt
说明：用方案 B（切分单元→LLM 编辑操作→确定性重组）。默认保守口径。
注意：实验表明精简可能丢信息/引入错误，重要内容请人工核对。
"""
import os
import sys
import argparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))
from scripts.llm_client import LLMClient, load_config  # noqa: E402
from scripts.segment import segment  # noqa: E402
from schemes.scheme_b_rewrite import apply_scheme_B  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="LLM 输出精简（方案 B，保守口径）")
    ap.add_argument("--text", help="直接传入要精简的文本")
    ap.add_argument("--input", help="输入文本文件路径（UTF-8）")
    ap.add_argument("--out", help="输出文件路径；不给则打印到终端")
    args = ap.parse_args()

    if args.input:
        with open(args.input, encoding="utf-8") as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        print("需要 --text 或 --input 之一", file=sys.stderr)
        sys.exit(1)
    if not text.strip():
        print("输入为空", file=sys.stderr)
        sys.exit(1)

    client = LLMClient(load_config(os.path.join(ROOT, "config.yaml")), phase="dev")
    units = segment(text)
    result = apply_scheme_B(client, units, return_details=True)
    simp = result["text"]

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(simp)
        print(f"已写入 {args.out}", file=sys.stderr)
    else:
        print(simp)

    red = (len(text) - len(simp)) / max(len(text), 1) * 100
    ops = {}
    for op in result["ops"]:
        ops[op.get("op")] = ops.get(op.get("op"), 0) + 1
    print(f"[统计] 原文 {len(text)} 字符 → 精简 {len(simp)} 字符（降 {red:.1f}%）；"
          f"单元 {len(units)}；操作 {ops}；费用约 ¥{client.spent:.4f}", file=sys.stderr)
    print("[提醒] 精简可能丢信息/引入错误，重要内容请人工核对。", file=sys.stderr)


if __name__ == "__main__":
    main()
