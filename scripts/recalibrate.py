"""κ 重测：G1（保守口径）新批 vs 用户新批标注。
用户标完 recal_annotation.html 导出放 human/gold/recal_user/gold_user_annotations.json。
运行：.venv\\Scripts\\python.exe -m scripts.recalibrate
"""
import os
import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from scripts.run_calibration import compute_calibration, _load_dir  # noqa: E402
from scripts.ingest_gold import split_annotations  # noqa: E402


def main():
    src = os.path.join(ROOT, "human", "gold", "recal_user", "gold_user_annotations.json")
    if not os.path.exists(src):
        print("NO_RECAL_USER（请标完 recal_annotation.html 导出放 human/gold/recal_user/）")
        return
    user = split_annotations(json.load(open(src, encoding="utf-8")))
    g1 = _load_dir(os.path.join(ROOT, "annotations", "g1_recal"))
    cal = compute_calibration(user, g1)
    print("RECAL_CALIBRATION", json.dumps(cal, ensure_ascii=False))
    gate = cal["kappa_label"] >= 0.6 and cal["kappa_pathology"] >= 0.6
    print("GATE_kappa_ge_0.6", gate)
    print("RECAL_DONE")


if __name__ == "__main__":
    main()
