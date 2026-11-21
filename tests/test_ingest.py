"""金标导出接收纯逻辑单元测试。"""
import unittest

from scripts.ingest_gold import split_annotations


class IngestTests(unittest.TestCase):
    def test_split_array(self):
        data = [{"response_id": "r1", "units": []}, {"response_id": "r2", "units": []}]
        d = split_annotations(data)
        self.assertEqual(set(d), {"r1", "r2"})

    def test_split_single_dict(self):
        d = split_annotations({"response_id": "r1", "units": []})
        self.assertEqual(set(d), {"r1"})


if __name__ == "__main__":
    unittest.main()
