"""阶段 4 单元切分单元测试（SPEC §8.1）。重点：代码块整块=1单元且逐字节保留。"""
import unittest

from scripts.segment import segment


class SegTests(unittest.TestCase):
    def test_code_block_byte_exact(self):
        code = "```python\ndef add(a,b):\n    return a+b\n```"
        text = "前言。\n" + code + "\n后语。"
        units = segment(text)
        codes = [u for u in units if u["type"] == "code"]
        self.assertEqual(len(codes), 1)
        self.assertEqual(codes[0]["text"], code)  # 逐字节一致

    def test_heading(self):
        units = segment("# 标题\n\n正文。")
        self.assertEqual(units[0]["type"], "heading")
        self.assertEqual(units[0]["text"], "# 标题")

    def test_list_items(self):
        units = segment("- 甲\n- 乙\n- 丙")
        items = [u for u in units if u["type"] == "list_item"]
        self.assertEqual(len(items), 3)

    def test_table_rows(self):
        units = segment("| a | b |\n|---|---|\n| 1 | 2 |")
        rows = [u for u in units if u["type"] == "table_row"]
        self.assertEqual(len(rows), 3)

    def test_chinese_sentences(self):
        units = segment("你好。世界！测试？")
        texts = [u["text"] for u in units if u["type"] == "text"]
        self.assertEqual(texts, ["你好。", "世界！", "测试？"])

    def test_english_sentences(self):
        units = segment("Hello world. How are you?")
        texts = [u["text"] for u in units if u["type"] == "text"]
        self.assertEqual(len(texts), 2)

    def test_uid_sequential(self):
        units = segment("# H\n\n- a\n\n正文。第二句。")
        self.assertEqual([u["uid"] for u in units], [1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
