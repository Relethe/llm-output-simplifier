"""病理统计 + 理论上限单元测试（SPEC §8.6）。"""
import unittest

from eval.pathology import pathology_stats, theoretical_ceiling

SPEEDS = {"english_text": {"value": 238}, "chinese_text": {"value": None},
          "code": {"value": 119}, "table_row": {"value": 119}, "list_item": {"value": 119}}


class PathologyTests(unittest.TestCase):
    def test_pathology_stats(self):
        anns = [{"category": "问答", "model": "dev1",
                 "units": [{"type": "text", "text": "hello world", "pathology": ["P1"]},
                           {"type": "text", "text": "foo bar", "pathology": []}]}]
        s = pathology_stats(anns, SPEEDS)
        self.assertEqual(s["total_units"], 2)
        self.assertEqual(s["per_pathology"]["P1"]["count"], 1)
        self.assertAlmostEqual(s["per_pathology"]["P1"]["unit_frac"], 0.5)
        self.assertIn("P1|问答|dev1", s["cross"])

    def test_theoretical_ceiling_reduces(self):
        units = [{"uid": 1, "type": "text", "text": "hello world", "label": "删"},
                 {"uid": 2, "type": "text", "text": "foo bar baz", "label": "压"},
                 {"uid": 3, "type": "text", "text": "answer here", "label": "留", "move_first": True}]
        r = theoretical_ceiling(units, SPEEDS, 0, 3)
        self.assertLess(r["t_total_ceiling"], r["t_total_orig"])
        self.assertGreater(r["t_total_red_pct"], 0)
        # 删(2词)移除 + 压(3词×0.6) + 留(2词)前移 → ceiling=(2+1.8)/238*60
        self.assertAlmostEqual(r["t_total_ceiling"], (2 + 1.8) / 238 * 60, places=4)

    def test_ceiling_move_first_front(self):
        units = [{"uid": 1, "type": "text", "text": "padding text here", "label": "留"},
                 {"uid": 2, "type": "text", "text": "answer", "label": "留", "move_first": True}]
        r = theoretical_ceiling(units, SPEEDS, 0, 2)
        self.assertLess(r["t_answer_ceiling"], r["t_answer_orig"])  # 答案前移→T_答降


if __name__ == "__main__":
    unittest.main()
