"""Cohen's κ 单元测试。"""
import unittest

from eval.kappa import cohen_kappa, pathology_kappa


class KappaTests(unittest.TestCase):
    def test_perfect(self):
        self.assertAlmostEqual(cohen_kappa(["删", "压", "留"], ["删", "压", "留"]), 1.0)

    def test_zero(self):
        self.assertAlmostEqual(cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"]), 0.0)

    def test_partial(self):
        self.assertAlmostEqual(cohen_kappa(["yes", "yes", "no", "no"],
                                           ["yes", "no", "no", "no"]), 0.5)

    def test_length_mismatch(self):
        with self.assertRaises(ValueError):
            cohen_kappa(["a"], ["a", "b"])

    def test_pathology_perfect(self):
        u1 = [{"pathology": ["P1", "P3"]}, {"pathology": []}]
        u2 = [{"pathology": ["P1", "P3"]}, {"pathology": []}]
        self.assertAlmostEqual(pathology_kappa(u1, u2), 1.0)

    def test_pathology_no_pathologies(self):
        u1 = [{"pathology": []}, {"pathology": []}]
        self.assertAlmostEqual(pathology_kappa(u1, u1), 1.0)


if __name__ == "__main__":
    unittest.main()
