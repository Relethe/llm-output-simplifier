"""阶段 6 统计单元测试。"""
import unittest

from eval.stats import bootstrap_ci, holm


class StatsTests(unittest.TestCase):
    def test_bootstrap_ci_contains_mean(self):
        diffs = [5.0] * 50
        mean, lo, hi = bootstrap_ci(diffs, n=2000, seed=42)
        self.assertAlmostEqual(mean, 5.0, places=6)
        self.assertLessEqual(lo, 5.0)
        self.assertGreaterEqual(hi, 5.0)

    def test_bootstrap_ci_deterministic(self):
        diffs = list(range(1, 41))
        a = bootstrap_ci(diffs, n=1000, seed=42)
        b = bootstrap_ci(diffs, n=1000, seed=42)
        self.assertEqual(a, b)

    def test_bootstrap_ci_width(self):
        diffs = [1.0, 2.0, 3.0, 4.0, 5.0] * 10
        mean, lo, hi = bootstrap_ci(diffs, n=3000, seed=42)
        self.assertAlmostEqual(mean, 3.0, places=6)
        self.assertLess(lo, mean)
        self.assertGreater(hi, mean)

    def test_holm_known(self):
        adj = holm([0.01, 0.04, 0.03])
        self.assertAlmostEqual(adj[0], 0.03, places=6)
        self.assertAlmostEqual(adj[1], 0.06, places=6)
        self.assertAlmostEqual(adj[2], 0.06, places=6)

    def test_holm_monotone_and_cap(self):
        raw = [0.5, 0.9, 0.001]
        adj = holm(raw)
        for r, a in zip(raw, adj):
            self.assertGreaterEqual(a + 1e-9, r)
            self.assertLessEqual(a, 1.0)


if __name__ == "__main__":
    unittest.main()
