"""方案 B 确定性重组单元测试（SPEC §9.2 硬约束）。"""
import unittest

from scripts.segment import segment
from schemes.scheme_b import apply_edits


class SchemeBTests(unittest.TestCase):
    def setUp(self):
        self.code = "```python\nx = 1\nprint(x)\n```"
        self.units = segment("前言句。\n" + self.code + "\n- 列表甲\n- 列表乙\n结尾句。")

    def _ops(self, op):
        return [{"uid": u["uid"], "op": op} for u in self.units]

    def test_code_byte_exact_after_keep(self):
        out, san = apply_edits(self.units, self._ops("keep"))
        codes = [u["text"] for u in segment(out) if u["type"] == "code"]
        self.assertEqual(codes, [self.code])  # 逐字节一致
        self.assertEqual(san, [])

    def test_delete_removes_unit(self):
        target = next(u for u in self.units if u["text"] == "前言句。")
        edits = [{"uid": u["uid"], "op": ("delete" if u["uid"] == target["uid"] else "keep")}
                 for u in self.units]
        out, _ = apply_edits(self.units, edits)
        self.assertNotIn("前言句。", out)

    def test_compress_replaces_text(self):
        target = next(u for u in self.units if u["text"] == "结尾句。")
        edits = [{"uid": u["uid"], "op": ("compress" if u["uid"] == target["uid"] else "keep"),
                  **({"text": "尾。"} if u["uid"] == target["uid"] else {})} for u in self.units]
        out, _ = apply_edits(self.units, edits)
        self.assertIn("尾。", out)
        self.assertNotIn("结尾句。", out)

    def test_move_first_to_front(self):
        target = next(u for u in self.units if u["text"] == "结尾句。")
        edits = [{"uid": u["uid"], "op": ("move_first" if u["uid"] == target["uid"] else "keep")}
                 for u in self.units]
        out, _ = apply_edits(self.units, edits)
        self.assertTrue(out.startswith("结尾句。"))

    def test_code_compress_sanitized_to_keep(self):
        code_uid = next(u["uid"] for u in self.units if u["type"] == "code")
        edits = [{"uid": u["uid"], "op": ("compress" if u["uid"] == code_uid else "keep"),
                  **({"text": "HACKED"} if u["uid"] == code_uid else {})} for u in self.units]
        out, san = apply_edits(self.units, edits)
        self.assertIn(code_uid, san)
        self.assertNotIn("HACKED", out)
        codes = [u["text"] for u in segment(out) if u["type"] == "code"]
        self.assertEqual(codes, [self.code])  # 代码未被篡改

    def test_move_first_max_one(self):
        texts = [u for u in self.units if u["type"] == "list_item"]
        edits = [{"uid": u["uid"], "op": ("move_first" if u["uid"] in {texts[0]["uid"], texts[1]["uid"]} else "keep")}
                 for u in self.units]
        out, san = apply_edits(self.units, edits)
        self.assertEqual(len(san), 1)  # 第二个 move_first 被 sanitize
        self.assertTrue(out.startswith("- 列表甲"))  # 列表项单元含 markdown 前缀


if __name__ == "__main__":
    unittest.main()
