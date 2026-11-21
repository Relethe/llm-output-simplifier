"""阶段 4 标注 prompt / 解析 / 金标分层单元测试。"""
import unittest

from scripts.annotation_prompts import (
    build_system_prompt, build_annotation_messages, parse_annotation_json, PATHOLOGY_TABLE,
)
from scripts.make_gold_set import stratified_gold


class AnnotationTests(unittest.TestCase):
    def test_pathology_table_11(self):
        self.assertEqual(len(PATHOLOGY_TABLE), 11)

    def test_g1_g2_differ(self):
        self.assertNotEqual(build_system_prompt("G1"), build_system_prompt("G2"))

    def test_both_contain_all_pathologies(self):
        for v in ("G1", "G2"):
            p = build_system_prompt(v)
            for code, _, _, _ in PATHOLOGY_TABLE:
                self.assertIn(code, p)

    def test_messages_structure(self):
        units = [{"uid": 1, "type": "text", "text": "x"}]
        msgs = build_annotation_messages("dev_001_dev1", "问题", units, "G1")
        self.assertEqual(msgs[0]["role"], "system")
        self.assertIn("dev_001_dev1", msgs[1]["content"])
        self.assertIn("问题", msgs[1]["content"])

    def test_parse_bare_json(self):
        obj = parse_annotation_json('{"intent":"normal","units":[]}')
        self.assertEqual(obj["intent"], "normal")

    def test_parse_fenced_json(self):
        obj = parse_annotation_json('前言\n```json\n{"intent":"style_requested"}\n```\n后语')
        self.assertEqual(obj["intent"], "style_requested")

    def test_stratified_gold_coverage(self):
        items = []
        for c in ["问答", "代码", "解释", "建议"]:
            for role in ["dev1", "dev2"]:
                for i in range(25):
                    items.append({"category": c, "role": role, "id": f"{c}_{role}_{i}"})
        sel = stratified_gold(items, n=30, seed=42)
        self.assertEqual(len(sel), 30)
        cells = {(x["category"], x["role"]) for x in sel}
        self.assertEqual(len(cells), 8)  # 四类×两模型全覆盖
        self.assertEqual({x["category"] for x in sel}, {"问答", "代码", "解释", "建议"})
        self.assertEqual({x["role"] for x in sel}, {"dev1", "dev2"})

    def test_stratified_gold_deterministic(self):
        items = [{"category": "问答", "role": "dev1", "id": str(i)} for i in range(50)]
        self.assertEqual(stratified_gold(items, 10, 42), stratified_gold(items, 10, 42))


if __name__ == "__main__":
    unittest.main()
