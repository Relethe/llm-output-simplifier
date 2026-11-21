"""自定义代码测试 runner 单元测试（子进程跑 base 测试）。"""
import os
import unittest

import evalplus.data.utils as _u
_u.CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "evalplus-cache")
import evalplus.data as _d
_d.CACHE_DIR = _u.CACHE_DIR
from evalplus.data import get_human_eval_plus  # noqa: E402
from scripts.run_code_test import run_base_test  # noqa: E402


class CodeTestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problems = get_human_eval_plus()

    def test_canonical_passes(self):
        p = self.problems["HumanEval/0"]
        sol = p["prompt"] + p["canonical_solution"]
        self.assertTrue(run_base_test(sol, p))

    def test_wrong_solution_fails(self):
        p = self.problems["HumanEval/0"]
        sol = "def has_close_elements(numbers, threshold):\n    return False\n"
        self.assertFalse(run_base_test(sol, p))

    def test_timeout_fails(self):
        p = self.problems["HumanEval/0"]
        sol = "def has_close_elements(numbers, threshold):\n    while True:\n        pass\n"
        self.assertFalse(run_base_test(sol, p, timeout=2))


if __name__ == "__main__":
    unittest.main()
