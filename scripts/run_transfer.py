"""阶段 7.2 留出模型迁移（SPEC §11.2，全自动）。证据类型：实测（T_总公式）+ AI 代理（保留率裁判）。
test 100 × (2 开发 + 1 留出 Kimi) 生成→最优方案→判据：
留出 T_总降幅 ≥ 开发平均的 70%，保留率 ≥95%。留出 Kimi 仅阶段 7 解锁（phase=test）。
transfer_pass 为纯函数（可单测）；main 在阶段 7 接 test 回答与最优方案后跑。
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def transfer_pass(holdout_red, dev_reds, retention, ratio=0.70, ret_min=0.95):
    if not dev_reds:
        return False
    dev_avg = sum(dev_reds) / len(dev_reds)
    return holdout_red >= ratio * dev_avg and retention >= ret_min


def main():
    # 阶段 7 部署 glue：load prompts_test → dev1/dev2/holdout(phase=test) 生成 → 最优方案精简
    # → 各模型 T_总降幅 + 保留率裁判 → transfer_pass。须 Kimi 解锁 + 最优方案已定（阶段 6/8）。
    print("迁移测试：test 100×(2开发+Kimi)→最优方案；留出降幅≥开发均值70% 且 保留率≥95%")
    print("TRANSFER_SKELETON（须阶段7解锁Kimi+最优方案已定）")


if __name__ == "__main__":
    main()
