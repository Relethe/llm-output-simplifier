"""金标合并纯逻辑单元测试。"""
import unittest

from scripts.merge_gold import is_chinese, fill_units


class MergeGoldTests(unittest.TestCase):
    def test_is_chinese(self):
        self.assertTrue(is_chinese("Chinese"))
        self.assertFalse(is_chinese("English"))
        self.assertFalse(is_chinese("Japanese"))

    def test_fill_units(self):
        ai_obj = {"response_id": "r1", "units": [{"uid": 1, "label": "删", "pathology": ["P1"]}]}
        cand = [{"uid": 1, "type": "text", "text": "hello"}, {"uid": 2, "type": "text", "text": "world"}]
        out = fill_units(ai_obj, cand)
        self.assertEqual(out["units"][0]["text"], "hello")
        self.assertEqual(out["units"][0]["label"], "删")
        self.assertEqual(out["units"][1]["label"], "留")  # AI 未标 → 默认留


if __name__ == "__main__":
    unittest.main()
