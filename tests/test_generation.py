"""阶段 3 生成纯逻辑单元测试（无 API 费用）。"""
import json
import os
import tempfile
import unittest

from scripts.generate_responses import build_entry, load_done


class GenTests(unittest.TestCase):
    def test_build_entry_fields(self):
        prompt = {"id": "dev_001", "text": "q"}
        meta = {"model": "deepseek-v4.1-flash-1017", "model_version": "deepseek-v4.1-flash-1017",
                "params": {}, "tokens_out": 43, "latency_ms": 1477.5,
                "timestamp": "2026-11-20T00:00:00+00:00"}
        e = build_entry(prompt, "dev1", meta, "answer")
        self.assertEqual(e["response_id"], "dev_001_dev1")
        self.assertEqual(e["prompt_id"], "dev_001")
        for k in ["response_id", "prompt_id", "model", "model_version", "params",
                  "response", "tokens_out", "latency_ms", "timestamp"]:
            self.assertIn(k, e)
        self.assertEqual(e["response"], "answer")
        self.assertEqual(e["tokens_out"], 43)

    def test_load_done(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.jsonl")
            with open(p, "w", encoding="utf-8") as f:
                f.write(json.dumps({"response_id": "dev_001_dev1"}) + "\n")
                f.write(json.dumps({"response_id": "dev_001_dev2"}) + "\n")
            self.assertEqual(load_done(p), {"dev_001_dev1", "dev_001_dev2"})
            self.assertEqual(load_done(os.path.join(d, "none.jsonl")), set())


if __name__ == "__main__":
    unittest.main()
