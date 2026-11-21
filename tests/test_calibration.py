"""阶段 4 校准 + 放量编排纯逻辑单元测试。"""
import unittest

from scripts.run_calibration import compute_calibration, finalize_annotations


def ann(rid, units, points):
    return {"response_id": rid, "annotator": "G1", "intent": "normal",
            "correctness_issue": None, "must_keep_points": points, "units": units}


class CalibrationTests(unittest.TestCase):
    def test_calibration_perfect(self):
        units = [{"uid": 1, "label": "删", "pathology": ["P1"]},
                 {"uid": 2, "label": "留", "pathology": []}]
        user = {"r1": ann("r1", units, [{"pid": 1, "text": "x"}])}
        g1 = {"r1": ann("r1", units, [{"pid": 1, "text": "x"}])}
        cal = compute_calibration(user, g1)
        self.assertAlmostEqual(cal["kappa_label"], 1.0)
        self.assertEqual(cal["n_units"], 2)

    def test_calibration_disagree(self):
        u_units = [{"uid": 1, "label": "删", "pathology": []}, {"uid": 2, "label": "留", "pathology": []}]
        g_units = [{"uid": 1, "label": "留", "pathology": []}, {"uid": 2, "label": "留", "pathology": []}]
        cal = compute_calibration({"r": ann("r", u_units, [])}, {"r": ann("r", g_units, [])})
        self.assertLess(cal["kappa_label"], 1.0)

    def test_finalize_union_and_conservative(self):
        g1 = {"r1": ann("r1", [{"uid": 1, "type": "text", "text": "x", "label": "删", "pathology": []}],
                        [{"pid": 1, "text": "甲"}])}
        g2 = {"r1": ann("r1", [{"uid": 1, "type": "text", "text": "x", "label": "留", "pathology": []}],
                        [{"pid": 1, "text": "乙"}])}
        final, disagree = finalize_annotations(g1, g2)
        self.assertEqual(final["r1"]["units"][0]["label"], "留")  # 保守 删vs留→留
        self.assertEqual([p["text"] for p in final["r1"]["must_keep_points"]], ["甲", "乙"])  # 并集
        self.assertEqual(len(disagree), 1)
        self.assertEqual(disagree[0]["conservative"], "留")

    def test_finalize_no_disagreement(self):
        units = [{"uid": 1, "type": "text", "text": "x", "label": "留", "pathology": []}]
        g1 = {"r1": ann("r1", units, [{"pid": 1, "text": "甲"}])}
        g2 = {"r1": ann("r1", units, [{"pid": 1, "text": "甲"}])}
        final, disagree = finalize_annotations(g1, g2)
        self.assertEqual(len(disagree), 0)
        self.assertEqual(len(final["r1"]["must_keep_points"]), 1)  # 去重


if __name__ == "__main__":
    unittest.main()
