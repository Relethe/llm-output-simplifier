"""T0.2 单元测试：调用日志字段、预算熔断、留出锁、成本累计持久化。
用 mock 替换真实 API 调用（_invoke），不产生费用、不依赖密钥。
运行：.venv\\Scripts\\python.exe -m unittest discover -s tests -v
"""
import json
import os
import tempfile
import types
import unittest

from scripts.llm_client import (
    LLMClient, HoldoutLockedError, BudgetExceededError, load_config,
)


def fake_resp(text="ok", model="deepseek-chat", tin=10, tout=20):
    return types.SimpleNamespace(
        choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=text))],
        usage=types.SimpleNamespace(prompt_tokens=tin, completion_tokens=tout),
        model=model,
    )


def make_cfg(cap=100.0):
    return {
        "seed": 42,
        "budget": {"cap_cny": cap, "spent_cny": 0.0},
        "pricing_cny_per_mtok": {
            "deepseek-chat": {"in": 4, "out": 12},
            "moonshot-v1-8k": {"in": 12, "out": 12},
        },
        "models": {
            "dev": [{"role": "dev1", "family": "deepseek", "model": "deepseek-chat",
                     "base_url": "https://api.deepseek.com/v1", "api_key_env": "DEEPSEEK_API_KEY"}],
            "rewriter": {"family": "qwen", "model": "qwen2.5-7b-instruct",
                         "base_url": "x", "api_key_env": "DASHSCOPE_API_KEY"},
            "judge": {"family": "glm", "model": "glm-4-flash",
                      "base_url": "x", "api_key_env": "GLM_API_KEY"},
            "holdout": {"family": "kimi", "model": "moonshot-v1-8k", "base_url": "x",
                        "api_key_env": "MOONSHOT_API_KEY", "dev_phase_locked": True},
        },
        "generation": {"system_prompt": None, "temperature": None, "max_tokens": None, "n": 1},
    }


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = os.path.join(self.tmp.name, "calls.jsonl")
        self.budget = os.path.join(self.tmp.name, "budget_state.json")

    def tearDown(self):
        self.tmp.cleanup()

    def _client(self, cfg=None, phase="dev"):
        return LLMClient(cfg or make_cfg(), phase=phase, log_path=self.log,
                         budget_path=self.budget, env_file=None)

    def test_call_logs_required_fields(self):
        c = self._client()
        c._invoke = lambda *a, **k: fake_resp(text="你好", tin=10, tout=20)
        res = c.call("dev1", [{"role": "user", "content": "hi"}])
        self.assertEqual(res["text"], "你好")
        with open(self.log, encoding="utf-8") as f:
            entry = json.loads(f.readline())
        for field in ("timestamp", "role", "model", "model_version", "params",
                      "tokens_in", "tokens_out", "latency_ms", "cost_cny_est", "phase"):
            self.assertIn(field, entry)
        self.assertEqual(entry["tokens_in"], 10)
        self.assertEqual(entry["tokens_out"], 20)
        self.assertEqual(entry["model"], "deepseek-chat")
        self.assertGreaterEqual(entry["latency_ms"], 0)

    def test_responses_protocol_parsing(self):
        cfg = make_cfg()
        cfg["models"]["dev"][0]["api_protocol"] = "responses"
        c = self._client(cfg=cfg)
        fake = types.SimpleNamespace(
            output_text="答案", model="qwen4-max",
            usage=types.SimpleNamespace(input_tokens=7, output_tokens=9))
        c._invoke = lambda *a, **k: fake
        res = c.call("dev1", [{"role": "user", "content": "hi"}])
        self.assertEqual(res["text"], "答案")
        self.assertEqual(res["meta"]["tokens_in"], 7)
        self.assertEqual(res["meta"]["tokens_out"], 9)

    def test_budget_breaker_blocks_and_no_api_call(self):
        c = self._client(cfg=make_cfg(cap=100.0))
        c.spent = 100.0  # 已达上限

        def boom(*a, **k):
            raise AssertionError("API 不应被调用")
        c._invoke = boom
        with self.assertRaises(BudgetExceededError):
            c.call("dev1", [{"role": "user", "content": "hi"}])

    def test_holdout_locked_in_dev_phase(self):
        c = self._client(phase="dev")

        def boom(*a, **k):
            raise AssertionError("留出模型开发期不应被调用")
        c._invoke = boom
        with self.assertRaises(HoldoutLockedError):
            c.call("holdout", [{"role": "user", "content": "hi"}])

    def test_holdout_allowed_in_test_phase(self):
        c = self._client(phase="test")
        c._invoke = lambda *a, **k: fake_resp(text="迁移", model="moonshot-v1-8k")
        res = c.call("holdout", [{"role": "user", "content": "hi"}])
        self.assertEqual(res["text"], "迁移")

    def test_cost_accumulates_and_persists(self):
        c = self._client()
        c._invoke = lambda *a, **k: fake_resp(tin=1_000_000, tout=1_000_000)
        c.call("dev1", [{"role": "user", "content": "hi"}])
        # deepseek in4/out12 每百万 → (4+12)=16 元
        self.assertAlmostEqual(c.spent, 16.0, places=6)
        with open(self.budget, encoding="utf-8") as f:
            self.assertAlmostEqual(json.load(f)["spent_cny"], 16.0, places=6)
        # 新客户端从持久化状态恢复累计
        c2 = self._client()
        self.assertAlmostEqual(c2.spent, 16.0, places=6)

    def test_retry_on_transient_error(self):
        from openai import APIConnectionError
        import scripts.llm_client as mod
        c = self._client()
        n = {"count": 0}

        def flaky(*a, **k):
            n["count"] += 1
            if n["count"] < 3:
                raise APIConnectionError(request=None)
            return fake_resp(text="recovered")
        c._invoke = flaky
        orig_sleep = mod.time.sleep
        mod.time.sleep = lambda s: None  # 测试不真等
        try:
            res = c.call("dev1", [{"role": "user", "content": "hi"}])
        finally:
            mod.time.sleep = orig_sleep
        self.assertEqual(res["text"], "recovered")
        self.assertEqual(n["count"], 3)

    def test_responses_streaming_accumulation(self):
        from types import SimpleNamespace as NS

        class FakeResponses:
            def __init__(self, events):
                self.events = events

            def create(self, **kw):
                return iter(self.events)

        class FakeStreamClient:
            def __init__(self, events):
                self.responses = FakeResponses(events)
        events = [NS(type="response.output_text.delta", delta="你"),
                  NS(type="response.output_text.delta", delta="好"),
                  NS(type="response.completed",
                     response=NS(usage=NS(input_tokens=5, output_tokens=2), model="glm-5.3"))]
        c = self._client()
        resp = c._invoke(FakeStreamClient(events), "glm-5.3",
                         [{"role": "user", "content": "hi"}], {}, protocol="responses")
        self.assertEqual(resp.output_text, "你好")
        self.assertEqual(resp.usage.input_tokens, 5)
        self.assertEqual(resp.model, "glm-5.3")

    def test_streaming_wall_cap(self):
        from types import SimpleNamespace as NS

        class FakeResponses:
            def __init__(self, events):
                self.events = events

            def create(self, **kw):
                return iter(self.events)

        class FakeStreamClient:
            def __init__(self, events):
                self.responses = FakeResponses(events)
        events = [NS(type="response.output_text.delta", delta="x"),
                  NS(type="response.completed",
                     response=NS(usage=NS(input_tokens=1, output_tokens=1), model="m"))]
        c = self._client()
        resp = c._invoke(FakeStreamClient(events), "m", [{"role": "user", "content": "hi"}],
                         {}, protocol="responses", max_wall_s=-1)
        self.assertEqual(resp.output_text, "")  # 墙钟上限立即截断

    def test_load_real_config(self):
        cfg = load_config(os.path.join(os.path.dirname(__file__), "..", "config.yaml"))
        self.assertEqual(cfg["seed"], 42)
        self.assertEqual(cfg["budget"]["cap_cny"], 100)
        self.assertEqual(len(cfg["models"]["dev"]), 2)
        self.assertTrue(cfg["models"]["holdout"]["dev_phase_locked"])


if __name__ == "__main__":
    unittest.main()
