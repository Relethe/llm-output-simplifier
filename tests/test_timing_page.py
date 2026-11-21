"""计时阅读网页生成器单元测试。"""
import unittest

from scripts.make_timing_page import render_timing_page


class TimingPageTests(unittest.TestCase):
    def _items(self):
        return [{"id": "t1", "version": "original", "question": "q", "text": "正文",
                 "quiz": [{"q": "问题1", "a": "答1"}]}]

    def test_embeds_data(self):
        html = render_timing_page(self._items())
        self.assertIn("t1", html)
        self.assertNotIn("__DATA__", html)

    def test_has_timing_ui(self):
        html = render_timing_page(self._items())
        self.assertIn("开始阅读", html)
        self.assertIn("我读完了", html)
        self.assertIn("reading_ms", html)
        self.assertIn("performance.now", html)

    def test_no_lookback(self):
        html = render_timing_page(self._items())
        self.assertIn("text.classList.add('hidden')", html)  # 读完隐藏文本


if __name__ == "__main__":
    unittest.main()
