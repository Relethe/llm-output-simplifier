"""金标标注网页生成器单元测试。"""
import unittest

from scripts.make_gold_page import render_gold_page


class GoldPageTests(unittest.TestCase):
    def _items(self):
        return [{"response_id": "dev_001_dev1", "question": "q", "response": "r",
                 "category": "问答", "role": "dev1", "lang": "Chinese",
                 "units": [{"uid": 1, "type": "text", "text": "x"},
                           {"uid": 2, "type": "code", "text": "```\ny\n```"}]}]

    def test_embeds_data(self):
        html = render_gold_page(self._items())
        self.assertIn("dev_001_dev1", html)
        self.assertNotIn("__DATA__", html)

    def test_has_key_ui(self):
        html = render_gold_page(self._items())
        self.assertIn("金标标注", html)
        self.assertIn("exportGold", html)
        self.assertIn("style_requested", html)
        self.assertIn("move_first", html)

    def test_code_label_restriction(self):
        html = render_gold_page(self._items())
        self.assertIn("u.type==='code'?['留','删']", html)  # 代码块限删/留


if __name__ == "__main__":
    unittest.main()
