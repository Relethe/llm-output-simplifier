"""阶段 6 聚合/消融 + 阶段 7 EvalPlus 核心单元测试。"""
import unittest

from eval.aggregate import pct_reduction, retention_rate, summarize
from eval.ablation import ablation_A, ablation_B, ablation_F
from scripts.evalplus_harness import extract_code, pass_at_1
from scripts.run_eval import get_answer_uid


class EvalAggTests(unittest.TestCase):
    def test_pct_reduction(self):
        self.assertAlmostEqual(pct_reduction(100, 70), 30.0)
        self.assertEqual(pct_reduction(0, 0), 0.0)

    def test_retention_rate(self):
        self.assertAlmostEqual(retention_rate(19, 20), 0.95)
        self.assertEqual(retention_rate(0, 0), 1.0)

    def _item(self, cat, model, tt_o, tt_s, held, total, blind):
        return {"category": cat, "model": model, "t_total_orig": tt_o, "t_total_simp": tt_s,
                "t_answer_orig": tt_o / 2, "t_answer_simp": tt_s / 2,
                "held": held, "total": total, "new_errors": 0, "blind": blind}

    def test_summarize_structure(self):
        items = [self._item("问答", "dev1", 100, 70, 19, 20, "simplified"),
                 self._item("代码", "dev2", 200, 100, 20, 20, "tie")]
        s = summarize(items)
        self.assertEqual(s["overall"]["n"], 2)
        self.assertAlmostEqual(s["overall"]["t_total_red_mean"], 40.0)  # (30+50)/2
        self.assertIn("问答", s["by_category"])
        self.assertIn("dev2", s["by_model"])
        self.assertAlmostEqual(s["overall"]["retention"], 39 / 40)
        self.assertAlmostEqual(s["overall"]["blind_win_rate"], 0.5)

    def test_summarize_ci(self):
        items = [self._item("问答", "dev1", 100, 70, 20, 20, "simplified")] * 10
        s = summarize(items)
        lo, hi = s["overall"]["t_total_red_ci95"]
        self.assertLessEqual(lo, 30.0)
        self.assertGreaterEqual(hi, 30.0)

    def test_ablation_counts(self):
        self.assertEqual(len(ablation_A()), 12)  # full + 11
        self.assertEqual(len(ablation_B()), 4)
        self.assertEqual(len(ablation_F()), 2)
        self.assertEqual(ablation_A()[1]["remove"], 1)

    def test_extract_code_largest(self):
        resp = "前言\n```python\nx=1\n```\n中\n```python\ndef f():\n    return 2\n```\n尾"
        code = extract_code(resp)
        self.assertIn("def f()", code)
        self.assertNotIn("x=1", code)

    def test_extract_code_no_fence(self):
        self.assertEqual(extract_code("plain text"), "plain text")

    def test_pass_at_1(self):
        self.assertAlmostEqual(pass_at_1([True, True, False, True]), 0.75)
        self.assertEqual(pass_at_1([]), 0.0)

    def test_get_answer_uid_move_first(self):
        units = [{"uid": 1, "move_first": False}, {"uid": 2, "move_first": True}]
        self.assertEqual(get_answer_uid(units), 2)

    def test_get_answer_uid_default(self):
        self.assertEqual(get_answer_uid([{"uid": 1, "move_first": False}]), 1)


if __name__ == "__main__":
    unittest.main()
