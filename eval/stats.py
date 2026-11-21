"""阶段 6 统计（SPEC v0.2 §10.3）：配对 bootstrap 95% CI + Holm 多重比较校正。"""
import numpy as np


def bootstrap_ci(diffs, n=10000, seed=42, alpha=0.05):
    """配对差值的均值及 percentile bootstrap CI。返回 (mean, lo, hi)。"""
    diffs = np.asarray(diffs, dtype=float)
    n_obs = len(diffs)
    if n_obs == 0:
        return 0.0, 0.0, 0.0
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n_obs, size=(n, n_obs))
    means = diffs[idx].mean(axis=1)
    lo = float(np.percentile(means, 100 * alpha / 2))
    hi = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return float(diffs.mean()), lo, hi


def holm(pvalues):
    """Holm 逐步下降校正，返回原顺序的调整后 p 值（封顶 1）。"""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvalues[i])
        adj[i] = min(1.0, running)
    return adj
