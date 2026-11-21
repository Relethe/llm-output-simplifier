"""生成补缺纯逻辑单元测试。"""
import unittest

from scripts.fill_skipped import find_missing


class FillTests(unittest.TestCase):
    def test_find_missing(self):
        prompts = [{"id": "dev_001"}, {"id": "dev_002"}]
        present = {"dev_001_dev1", "dev_001_dev2", "dev_002_dev1"}
        self.assertEqual(find_missing(prompts, ["dev1", "dev2"], present), ["dev_002_dev2"])

    def test_find_missing_none(self):
        prompts = [{"id": "dev_001"}]
        present = {"dev_001_dev1", "dev_001_dev2"}
        self.assertEqual(find_missing(prompts, ["dev1", "dev2"], present), [])

    def test_find_missing_all(self):
        prompts = [{"id": "dev_001"}]
        self.assertEqual(find_missing(prompts, ["dev1", "dev2"], set()),
                         ["dev_001_dev1", "dev_001_dev2"])


if __name__ == "__main__":
    unittest.main()
