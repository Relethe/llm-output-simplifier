"""盲评校准 + 分歧裁决网页生成器单元测试。"""
import unittest

from scripts.make_blind_eval_page import render_blind_page
from scripts.make_adjudication_page import render_adjudication_page
from scripts.make_retention_check_page import render_retention_page


class HumanPageTests(unittest.TestCase):
    def test_blind_embeds_and_ui(self):
        items = [{"id": "p1", "text_a": "甲文", "text_b": "乙文"}]
        html = render_blind_page(items)
        self.assertIn("p1", html)
        self.assertNotIn("__DATA__", html)
        self.assertIn("更快拿到需要的信息", html)
        self.assertIn("一样", html)

    def test_blind_no_better_question(self):
        html = render_blind_page([{"id": "p1", "text_a": "a", "text_b": "b"}])
        self.assertIn("不是问“哪个更好”", html)

    def test_adjudication_embeds_and_ui(self):
        items = [{"response_id": "dev_001_dev1", "uid": 3, "type": "text",
                  "text": "x", "g1_label": "删", "g2_label": "留", "conservative": "留"}]
        html = render_adjudication_page(items)
        self.assertIn("dev_001_dev1", html)
        self.assertIn("G1: ", html)
        self.assertIn("保守暂采", html)
        self.assertIn("user_label", html)

    def test_adjudication_code_restriction(self):
        html = render_adjudication_page([{"response_id": "r", "uid": 1, "type": "code",
                                          "text": "c", "g1_label": "留", "g2_label": "删", "conservative": "留"}])
        self.assertIn("d.type==='code'?['留','删']", html)

    def test_retention_page(self):
        checks = [{"id": "c1", "point": "点", "simplified": "简", "judge_held": True}]
        errors = [{"response_id": "r1", "claim": "错误说法"}]
        html = render_retention_page(checks, errors)
        self.assertIn("c1", html)
        self.assertIn("错误说法", html)
        self.assertNotIn("__CHECKS__", html)
        self.assertNotIn("__ERRORS__", html)
        self.assertIn("逐条确认", html)
        self.assertIn("user_agree", html)


if __name__ == "__main__":
    unittest.main()
