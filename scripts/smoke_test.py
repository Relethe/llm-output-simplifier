"""阶段 0 冒烟测试：2 个开发模型各跑通 1 条请求（SPEC-CHANGE-001：原 3 改 2）。

运行前：.env 填好 DEEPSEEK_API_KEY / DASHSCOPE_API_KEY；config budget.cap_cny 已设。
运行：.venv\\Scripts\\python.exe scripts\\smoke_test.py
验收：dev1/dev2 各返回 1 条非空回答并落 logs/calls.jsonl；同时实测国内端点证书是否正常。
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.llm_client import LLMClient, load_config  # noqa: E402


def main():
    cfg = load_config(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml"))
    client = LLMClient(cfg, phase="dev")
    prompt = [{"role": "user", "content": "用一句话回答：1+1 等于几？"}]
    ok = True
    for role in ("dev1", "dev2"):
        try:
            res = client.call(role, prompt)
            text = (res["text"] or "").strip()
            m = res["meta"]
            print(f"[{role}] model={m['model']} version={m['model_version']} "
                  f"in={m['tokens_in']} out={m['tokens_out']} "
                  f"latency_ms={m['latency_ms']} cost≈¥{m['cost_cny_est']}")
            print(f"  回答: {text[:120]}")
            if text:
                print("  ✓ 非空")
            else:
                print("  ✗ 空回答")
                ok = False
        except Exception as e:
            print(f"[{role}] ✗ 失败: {type(e).__name__}: {e}")
            ok = False
    print(f"累计花费≈¥{client.spent:.4f} / 上限¥{client.cap}")
    print("SMOKE_OK" if ok else "SMOKE_FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
