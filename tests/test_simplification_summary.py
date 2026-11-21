"""简化批次汇总纯逻辑测试。"""
import unittest

from scripts.summarize_simplification import summarize_rows


class SimplificationSummaryTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(summarize_rows({"x": 1} if False else []), {"n": 0})

    def test_summary(self):
        rows = [
            {"model": "m1", "original_chars": 100, "simplified_chars": 60,
             "simplifier_role": "simplifier_external", "simplifier_meta": {"latency_ms": 10},
             "ops": [{"op": "delete"}, {"op": "keep"}]},
            {"model": "m1", "original_chars": 200, "simplified_chars": 100,
             "simplifier_role": "simplifier_fallback", "simplifier_meta": {"latency_ms": 20},
             "ops": [{"op": "compress"}]},
        ]
        s = summarize_rows(rows)
        self.assertEqual(s["n"], 2)
        self.assertAlmostEqual(s["mean_char_reduction_pct"], 45.0)
        self.assertEqual(s["simplifier_roles"]["simplifier_fallback"], 1)
        self.assertEqual(s["ops"]["delete"], 1)


if __name__ == "__main__":
    unittest.main()
