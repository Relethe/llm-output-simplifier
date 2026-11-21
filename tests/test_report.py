"""阶段 8 MVP 决策规则单元测试（SPEC §12 预登记）。"""
import unittest

from scripts.make_report import decide_mvp


def s(red, ret, err):
    return {"red_vs_baseline": red, "retention": ret, "new_errors": err}


class ReportTests(unittest.TestCase):
    def test_A_wins(self):
        self.assertEqual(decide_mvp(s(20, 0.96, 0), s(30, 0.97, 0), 0, True, True), "F+A")

    def test_B_wins_when_A_fails(self):
        self.assertEqual(decide_mvp(s(10, 0.96, 0), s(20, 0.96, 0), 0, True, True), "F+B")

    def test_both_fail(self):
        self.assertEqual(decide_mvp(s(10, 0.90, 0), s(10, 0.90, 0), 0, True, True), "回阶段4查理论上限")

    def test_requires_code_and_transfer(self):
        self.assertEqual(decide_mvp(s(20, 0.96, 0), s(20, 0.96, 0), 0, False, True), "回阶段4查理论上限")
        self.assertEqual(decide_mvp(s(20, 0.96, 0), s(20, 0.96, 0), 0, True, False), "回阶段4查理论上限")

    def test_new_errors_vs_baseline(self):
        # A 新增错误 > 基线 → A 不达标；B 达标 → F+B
        self.assertEqual(decide_mvp(s(20, 0.96, 2), s(20, 0.96, 0), 1, True, True), "F+B")

    def test_retention_threshold(self):
        self.assertEqual(decide_mvp(s(20, 0.94, 0), s(20, 0.95, 0), 0, True, True), "F+B")
