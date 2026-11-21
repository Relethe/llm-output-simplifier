"""方案 A 提示词单元测试（SPEC §9.1）。"""
import unittest

from schemes.scheme_a import build_messages, build_prompt, BASELINE_PROMPT, RULES


class SchemeATests(unittest.TestCase):
    def test_thirteen_rules(self):
        self.assertEqual(len(RULES), 13)

    def test_mode_A_has_system(self):
        msgs = build_messages("问题", mode="A")
        self.assertEqual(msgs[0]["role"], "system")
        self.assertIn("第一句直接给出答案", msgs[0]["content"])
        self.assertEqual(msgs[1]["content"], "问题")

    def test_baseline(self):
        msgs = build_messages("问题", mode="baseline")
        self.assertEqual(msgs[0]["content"], BASELINE_PROMPT)

    def test_off_no_system(self):
        msgs = build_messages("问题", mode="off")
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["role"], "user")

    def test_ablate_rule_1(self):
        p = build_prompt(remove=1)
        self.assertNotIn("1. 第一句", p)
        self.assertIn("2. 不复述", p)
        self.assertIn("11. 只在能帮助", p)  # 不误删 11

    def test_ablate_rule_11(self):
        p = build_prompt(remove=11)
        self.assertNotIn("11. 只在能帮助", p)
        self.assertIn("1. 第一句", p)


if __name__ == "__main__":
    unittest.main()
