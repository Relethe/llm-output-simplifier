"""标注合并逻辑单元测试（SPEC §8.5）。"""
import unittest

from scripts.annotate import resolve_label, merge_must_keep, validate_annotation, normalize_label


class AnnotateTests(unittest.TestCase):
    def test_resolve_conservative(self):
        self.assertEqual(resolve_label("删", "留"), "留")
        self.assertEqual(resolve_label("压", "删"), "压")
        self.assertEqual(resolve_label("留", "压"), "留")
        self.assertEqual(resolve_label("留", "留"), "留")

    def test_normalize_traditional(self):
        self.assertEqual(normalize_label("刪"), "删")
        self.assertEqual(normalize_label("壓"), "压")
        self.assertEqual(normalize_label("留"), "留")

    def test_resolve_traditional(self):
        self.assertEqual(resolve_label("刪", "留"), "留")
        self.assertEqual(resolve_label("壓", "刪"), "压")

    def test_merge_union_dedup(self):
        p1 = [{"pid": 1, "text": "甲"}, {"pid": 2, "text": "乙"}]
        p2 = [{"pid": 1, "text": "乙"}, {"pid": 2, "text": "丙"}]
        merged = merge_must_keep(p1, p2)
        self.assertEqual([m["text"] for m in merged], ["甲", "乙", "丙"])
        self.assertEqual([m["pid"] for m in merged], [1, 2, 3])

    def _valid(self):
        return {"response_id": "dev_001_dev1", "annotator": "G1", "intent": "normal",
                "correctness_issue": None, "must_keep_points": [{"pid": 1, "text": "x"}],
                "units": [{"uid": 1, "type": "text", "text": "x", "label": "留",
                           "move_first": False, "pathology": [], "note": ""}]}

    def test_validate_ok(self):
        self.assertEqual(validate_annotation(self._valid()), [])

    def test_validate_missing_field(self):
        obj = self._valid()
        del obj["intent"]
        self.assertTrue(any("intent" in e for e in validate_annotation(obj)))

    def test_validate_bad_label(self):
        obj = self._valid()
        obj["units"][0]["label"] = "删除"
        self.assertTrue(any("bad label" in e for e in validate_annotation(obj)))

    def test_validate_code_cannot_compress(self):
        obj = self._valid()
        obj["units"][0]["type"] = "code"
        obj["units"][0]["label"] = "压"
        self.assertTrue(any("code 不可压" in e for e in validate_annotation(obj)))


if __name__ == "__main__":
    unittest.main()
