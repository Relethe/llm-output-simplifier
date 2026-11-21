"""方案 C / F 核心逻辑单元测试。"""
import unittest

from schemes.scheme_c import build_logit_bias
from schemes.scheme_f import intent_classify, route_request, sentence_buffer


class SchemeCFTests(unittest.TestCase):
    def test_logit_bias_negative(self):
        enc = lambda text: [ord(text[0])] if text else []
        bm = build_logit_bias(enc, phrases=["Certainly", "总之"])
        self.assertEqual(bm[ord("C")], -100)
        self.assertEqual(bm[ord("总")], -100)

    def test_logit_bias_empty_phrase(self):
        enc = lambda text: []
        self.assertEqual(build_logit_bias(enc, phrases=[""]), {})

    def test_intent_creative(self):
        self.assertEqual(intent_classify("写一首关于春天的诗"), "creative_style")
        self.assertEqual(intent_classify("tell me a funny story"), "creative_style")

    def test_intent_code(self):
        self.assertEqual(intent_classify("写一个排序函数"), "code")

    def test_intent_other(self):
        self.assertEqual(intent_classify("什么是导数"), "other")

    def test_route_off(self):
        msgs = [{"role": "user", "content": "什么是导数"}]
        out, b = route_request(msgs, "off")
        self.assertEqual(out, msgs)
        self.assertFalse(b)

    def test_route_creative_passthrough(self):
        msgs = [{"role": "user", "content": "写一首诗"}]
        out, b = route_request(msgs, "full")
        self.assertEqual(out, msgs)  # 创作放行，不注入
        self.assertFalse(b)

    def test_route_light_injects_A(self):
        msgs = [{"role": "user", "content": "什么是导数"}]
        out, b = route_request(msgs, "light")
        self.assertEqual(out[0]["role"], "system")
        self.assertFalse(b)

    def test_route_full_flags_B(self):
        msgs = [{"role": "user", "content": "什么是导数"}]
        out, b = route_request(msgs, "full")
        self.assertTrue(b)

    def test_sentence_buffer(self):
        out = list(sentence_buffer(["你好", "。", "世界", "！", "残余"]))
        self.assertEqual(out, ["你好。", "世界！", "残余"])

    def test_sentence_buffer_no_boundary(self):
        self.assertEqual(list(sentence_buffer(["abc", "def"])), ["abcdef"])


if __name__ == "__main__":
    unittest.main()
