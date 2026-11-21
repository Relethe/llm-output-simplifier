"""人力材料数据填充纯逻辑单元测试。"""
import unittest

from scripts.prepare_human_data import (
    make_blind_pairs, find_disagreements, sample_retention_checks, assign_timing_versions,
)


class PrepareHumanDataTests(unittest.TestCase):
    def test_blind_pairs_count_and_fields(self):
        pairs = [{"id": f"p{i}", "original": f"o{i}", "simplified": f"s{i}"} for i in range(50)]
        out = make_blind_pairs(pairs, n=30, seed=42)
        self.assertEqual(len(out), 30)
        for x in out:
            self.assertIn("text_a", x)
            self.assertIn("text_b", x)
            self.assertIn("simplified_is_a", x)

    def test_blind_pairs_deterministic(self):
        pairs = [{"id": str(i), "original": "o", "simplified": "s"} for i in range(40)]
        self.assertEqual(make_blind_pairs(pairs, 30, 42), make_blind_pairs(pairs, 30, 42))

    def test_blind_pairs_both_orders_exist(self):
        pairs = [{"id": str(i), "original": "o", "simplified": "s"} for i in range(60)]
        out = make_blind_pairs(pairs, 30, 42)
        self.assertTrue(any(x["simplified_is_a"] for x in out))
        self.assertTrue(any(not x["simplified_is_a"] for x in out))

    def test_find_disagreements(self):
        g1 = [{"uid": 1, "type": "text", "text": "x", "label": "删"},
              {"uid": 2, "type": "text", "text": "y", "label": "留"}]
        g2 = [{"uid": 1, "type": "text", "text": "x", "label": "留"},
              {"uid": 2, "type": "text", "text": "y", "label": "留"}]
        d = find_disagreements(g1, g2)
        self.assertEqual(len(d), 1)
        self.assertEqual(d[0]["uid"], 1)
        self.assertEqual(d[0]["conservative"], "留")  # 删 vs 留 → 留

    def test_sample_retention_checks(self):
        res = [{"id": str(i)} for i in range(50)]
        self.assertEqual(len(sample_retention_checks(res, 30, 42)), 30)

    def test_assign_timing_versions_half(self):
        items = [{"id": str(i), "question": "q", "original": "o", "simplified": "s", "quiz": []}
                 for i in range(40)]
        out = assign_timing_versions(items, 42)
        self.assertEqual(len(out), 40)
        self.assertEqual(sum(1 for x in out if x["version"] == "original"), 20)
        self.assertEqual(sum(1 for x in out if x["version"] == "simplified"), 20)
        for x in out:
            self.assertEqual(x["text"], "o" if x["version"] == "original" else "s")


if __name__ == "__main__":
    unittest.main()
