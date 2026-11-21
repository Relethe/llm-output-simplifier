"""evalplus CLI 包装器：补丁 CACHE_DIR 到项目内可写目录后跑 evalplus.evaluate（fire 读 sys.argv）。
用法：python scripts/_evalplus_run.py humaneval --samples <file> --parallel 1
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "evalplus-cache")
os.makedirs(CACHE, exist_ok=True)
import evalplus.data.utils as _u  # noqa: E402
_u.CACHE_DIR = CACHE
import evalplus.data as _d  # noqa: E402
if hasattr(_d, "CACHE_DIR"):
    _d.CACHE_DIR = CACHE
from evalplus.evaluate import main  # noqa: E402

main()
