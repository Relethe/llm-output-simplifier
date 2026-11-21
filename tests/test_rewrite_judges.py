"""方案 B 改写 + 阶段 6 裁判单元测试（I/O 用 fake client）。"""
import unittest

from schemes.scheme_b_rewrite import build_rewrite_messages, parse_edit_ops, compress_is_subset, apply_scheme_B
from eval.judges import retention_judge, new_errors_judge, blind_eval


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.i = 0
        self.calls = []

    def call(self, role, msgs, **kw):
        self.calls.append((role, msgs, kw))
        r = self.responses[self.i % len(self.responses)]
        self.i += 1
        return {"text": r, "meta": {}}


class RewriteJudgeTests(unittest.TestCase):
    def test_parse_edit_ops_bare(self):
        ops = parse_edit_ops('[{"uid":1,"op":"delete"}]')
        self.assertEqual(ops[0]["op"], "delete")

    def test_parse_edit_ops_fenced(self):
        ops = parse_edit_ops('```json\n[{"uid":2,"op":"keep"}]\n```')
        self.assertEqual(ops[0]["uid"], 2)

    def test_rewrite_messages(self):
        units = [{"uid": 1, "type": "text", "text": "x"}]
        msgs = build_rewrite_messages(units, "样例")
        self.assertIn("编辑操作", msgs[0]["content"])
        self.assertIn("P1", msgs[0]["content"])
        self.assertIn("样例", msgs[0]["content"])

    def test_compress_subset_yes(self):
        self.assertTrue(compress_is_subset(FakeClient(["是"]), "原", "压"))

    def test_compress_subset_no(self):
        self.assertFalse(compress_is_subset(FakeClient(["否"]), "原", "压"))

    def test_retention_yes_no(self):
        self.assertTrue(retention_judge(FakeClient(["是"]), "点", "简"))
        self.assertFalse(retention_judge(FakeClient(["否"]), "点", "简"))

    def test_new_errors_parse(self):
        self.assertEqual(new_errors_judge(FakeClient(['["错误1"]']), "原", "简"), ["错误1"])
        self.assertEqual(new_errors_judge(FakeClient(["[]"]), "原", "简"), [])

    def test_blind_consistent(self):
        # r1: A左B右→A ; r2: B左A右→B(=A胜) 一致 → A
        self.assertEqual(blind_eval(FakeClient(["A", "B"]), "甲", "乙"), "A")

    def test_blind_inconsistent(self):
        # r1=A ; r2=A(=B胜) 不一致 → 一样
        self.assertEqual(blind_eval(FakeClient(["A", "A"]), "甲", "乙"), "一样")

    def test_blind_uses_effort(self):
        fc = FakeClient(["A", "B"])
        blind_eval(fc, "甲", "乙")
        self.assertTrue(all(kw.get("reasoning") == {"effort": "low"} for _, _, kw in fc.calls))

    def test_apply_scheme_B_compress_validated(self):
        units = [{"uid": 1, "type": "text", "text": "冗长开场白。"},
                 {"uid": 2, "type": "text", "text": "核心答案。"}]
        fc = FakeClient(['[{"uid":1,"op":"delete"},{"uid":2,"op":"compress","text":"答案。"}]', '是'])
        out = apply_scheme_B(fc, units)
        self.assertNotIn("冗长开场白", out)
        self.assertIn("答案。", out)

    def test_apply_scheme_B_disable_delete(self):
        units = [{"uid": 1, "type": "text", "text": "甲。"}, {"uid": 2, "type": "text", "text": "乙。"}]
        fc = FakeClient(['[{"uid":1,"op":"delete"},{"uid":2,"op":"keep"}]'])
        out = apply_scheme_B(fc, units, disable=["delete"])
        self.assertIn("甲。", out)  # delete 被禁→keep

    def test_apply_scheme_B_compress_rejected(self):
        units = [{"uid": 1, "type": "text", "text": "原句。"}]
        fc = FakeClient(['[{"uid":1,"op":"compress","text":"新增错误信息。"}]', '否'])
        out = apply_scheme_B(fc, units)
        self.assertIn("原句。", out)  # 校验否→回退 keep
        self.assertNotIn("新增错误", out)


if __name__ == "__main__":
    unittest.main()
