"""阶段 2 抽样纯逻辑单元测试（无 I/O、无 API 费用）。
运行：.venv\\Scripts\\python.exe -m unittest discover -s tests -v
"""
import unittest

from scripts.sample_prompts import (
    first_user_text, cheap_filter, normalize, is_chinese, select_quota, CATEGORIES,
)


class SamplingTests(unittest.TestCase):
    def test_first_user_text(self):
        self.assertEqual(first_user_text(
            [{"role": "user", "content": "hello world"}, {"role": "assistant", "content": "x"}]),
            "hello world")
        self.assertEqual(first_user_text(
            [{"role": "assistant", "content": "x"}, {"role": "user", "content": "q"}]), "q")
        self.assertIsNone(first_user_text([{"role": "assistant", "content": "x"}]))

    def test_cheap_filter_length(self):
        self.assertFalse(cheap_filter("short"))
        self.assertTrue(cheap_filter("a" * 10))
        self.assertTrue(cheap_filter("a" * 2000))
        self.assertFalse(cheap_filter("a" * 2001))

    def test_cheap_filter_flags(self):
        t = "a" * 50
        self.assertFalse(cheap_filter(t, flagged=True))
        self.assertFalse(cheap_filter(t, toxic=True))
        self.assertFalse(cheap_filter(t, redacted=True))
        self.assertTrue(cheap_filter(t))

    def test_cheap_filter_greeting(self):
        self.assertFalse(cheap_filter("hello there"))

    def test_normalize(self):
        self.assertEqual(normalize("Hello,  World!"), "hello world")

    def test_is_chinese(self):
        self.assertTrue(is_chinese("Chinese", "anything"))
        self.assertTrue(is_chinese("English", "你好世界测试中文"))
        self.assertFalse(is_chinese("English", "hello world"))

    def test_select_quota_full(self):
        items = []
        for c in CATEGORIES:
            for i in range(10):
                items.append({"text": f"{c}zh{i}", "category": c, "zh": True})
            for i in range(20):
                items.append({"text": f"{c}en{i}", "category": c, "zh": False})
        sel, stats = select_quota(items)
        self.assertEqual(len(sel), 100)
        for c in CATEGORIES:
            self.assertEqual(stats[c]["count"], 25)
            self.assertGreaterEqual(stats[c]["zh"], 8)
            self.assertFalse(stats[c]["zh_shortfall"])

    def test_select_quota_zh_shortfall(self):
        items = []
        for c in CATEGORIES:
            for i in range(3):
                items.append({"text": f"{c}zh{i}", "category": c, "zh": True})
            for i in range(30):
                items.append({"text": f"{c}en{i}", "category": c, "zh": False})
        sel, stats = select_quota(items)
        for c in CATEGORIES:
            self.assertEqual(stats[c]["count"], 25)
            self.assertTrue(stats[c]["zh_shortfall"])


if __name__ == "__main__":
    unittest.main()
