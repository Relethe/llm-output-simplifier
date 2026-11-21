"""阶段 6 阅读时间指标单元测试（SPEC §1.1/1.2）。"""
import unittest

from eval.metrics import (
    unit_length, structure_switches, t_total, t_answer, is_chinese,
)

SPEEDS = {
    "english_text": {"value": 238}, "chinese_text": {"value": None},
    "code": {"value": 119}, "table_row": {"value": 119}, "list_item": {"value": 119},
}


class MetricsTests(unittest.TestCase):
    def test_unit_length_english_words(self):
        self.assertEqual(unit_length({"type": "text", "text": "hello world"}), 2)

    def test_unit_length_chinese_chars(self):
        self.assertTrue(is_chinese("你好世界"))
        self.assertEqual(unit_length({"type": "text", "text": "你好世界"}), 4)

    def test_unit_length_code_lines(self):
        self.assertEqual(unit_length({"type": "code", "text": "a\nb\nc"}), 3)

    def test_unit_length_table_list(self):
        self.assertEqual(unit_length({"type": "table_row", "text": "| a | b |"}), 1)
        self.assertEqual(unit_length({"type": "list_item", "text": "- x"}), 1)

    def test_structure_switches(self):
        u = lambda t: {"type": t, "text": "x"}
        self.assertEqual(structure_switches([u("text"), u("code"), u("text")]), 2)
        self.assertEqual(structure_switches([u("text"), u("text")]), 0)
        self.assertEqual(structure_switches([u("heading"), u("text"), u("code")]), 2)

    def test_t_total(self):
        units = [{"uid": 1, "type": "text", "text": "hello world"},
                 {"uid": 2, "type": "code", "text": "a\nb\nc"}]
        expected = (2 / 238 + 3 / 119) * 60  # c=0, 1 switch 但 c=0
        self.assertAlmostEqual(t_total(units, SPEEDS, 0), expected, places=4)

    def test_t_total_with_c(self):
        units = [{"uid": 1, "type": "text", "text": "hello world"},
                 {"uid": 2, "type": "code", "text": "a\nb\nc"}]
        base = (2 / 238 + 3 / 119) * 60
        self.assertAlmostEqual(t_total(units, SPEEDS, 2.0), base + 2.0 * 1, places=4)

    def test_t_answer(self):
        units = [{"uid": 1, "type": "text", "text": "hello world"},
                 {"uid": 2, "type": "text", "text": "foo bar baz"}]
        expected = (2 / 238 + 3 / 238) * 60
        self.assertAlmostEqual(t_answer(units, SPEEDS, 0, 2), expected, places=4)
        self.assertAlmostEqual(t_answer(units, SPEEDS, 0, 1), (2 / 238) * 60, places=4)


if __name__ == "__main__":
    unittest.main()
