"""阶段 7 AI 读者测验 + 留出迁移判据单元测试。"""
import unittest

from scripts.ai_reader_test import (
    grade_answer, accuracy, filter_by_no_text, reader_test_pass,
    build_question_writer_messages, build_answerer_messages,
)
from scripts.run_transfer import transfer_pass


class ReaderTransferTests(unittest.TestCase):
    def test_grade_match(self):
        self.assertTrue(grade_answer("2", "2"))
        self.assertTrue(grade_answer("等于 2", "2"))

    def test_grade_not_found(self):
        self.assertFalse(grade_answer("找不到", "2"))
        self.assertFalse(grade_answer("", "2"))

    def test_accuracy(self):
        self.assertAlmostEqual(accuracy([True, False, True, True]), 0.75)
        self.assertEqual(accuracy([]), 0.0)

    def test_filter_no_text(self):
        items = [{"q": "a", "no_text_correct": True}, {"q": "b", "no_text_correct": False}]
        kept = filter_by_no_text(items)
        self.assertEqual([x["q"] for x in kept], ["b"])

    def test_reader_pass_threshold(self):
        self.assertTrue(reader_test_pass(0.90, 0.88))   # 降 2pp ≤3
        self.assertFalse(reader_test_pass(0.90, 0.85))  # 降 5pp >3
        self.assertTrue(reader_test_pass(0.90, 0.90))   # 降 0

    def test_question_writer_messages(self):
        msgs = build_question_writer_messages([{"pid": 1, "text": "x"}])
        self.assertIn("必留点", msgs[1]["content"])
        self.assertEqual(msgs[0]["role"], "system")

    def test_answerer_no_text(self):
        msgs = build_answerer_messages(None, ["q1"])
        self.assertIn("无文本", msgs[1]["content"])

    def test_transfer_pass(self):
        self.assertTrue(transfer_pass(20, [25, 25], 0.96))   # 20≥17.5, ret≥95
        self.assertFalse(transfer_pass(10, [25, 25], 0.96))  # 10<17.5
        self.assertFalse(transfer_pass(20, [25, 25], 0.90))  # ret<95
        self.assertFalse(transfer_pass(20, [], 0.96))
