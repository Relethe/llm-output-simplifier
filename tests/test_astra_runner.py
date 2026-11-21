"""Astra 批量简化 runner 的纯逻辑测试。"""
import json
import os
import tempfile
import unittest

from scripts.run_astra_simplification import load_done


class AstraRunnerTests(unittest.TestCase):
    def test_load_done_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(load_done(os.path.join(d, "missing.jsonl")), set())

    def test_load_done_ids(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.jsonl")
            with open(p, "w", encoding="utf-8") as f:
                f.write(json.dumps({"response_id": "r1"}) + "\n")
                f.write(json.dumps({"response_id": "r2"}) + "\n")
            self.assertEqual(load_done(p), {"r1", "r2"})
