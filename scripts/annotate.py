"""阶段 4 标注合并逻辑（SPEC v0.2 §8.5）：必留点并集、分歧保守裁决、schema 校验。"""

LABEL_RANK = {"删": 0, "压": 1, "留": 2}
_TRAD_LABEL = {"刪": "删", "壓": "压", "留": "留"}
REQUIRED_TOP = ["response_id", "annotator", "intent", "correctness_issue",
                "must_keep_points", "units"]
REQUIRED_UNIT = ["uid", "type", "text", "label", "move_first", "pathology", "note"]


def normalize_label(label):
    return _TRAD_LABEL.get(label, label)


def resolve_label(a, b):
    """G1/G2 label 一致则采纳；不一致取保守（保留更多）：留 > 压 > 删。"""
    a, b = normalize_label(a), normalize_label(b)
    if a == b:
        return a
    return a if LABEL_RANK[a] >= LABEL_RANK[b] else b


def merge_must_keep(pts1, pts2):
    """必留点取 G1∪G2 并集（按 text 去重），重编 pid。分母偏大、结论保守。"""
    seen = set()
    out = []
    for p in list(pts1) + list(pts2):
        t = p["text"].strip()
        if t and t not in seen:
            seen.add(t)
            out.append({"pid": len(out) + 1, "text": p["text"]})
    return out


def validate_annotation(obj):
    errs = []
    for k in REQUIRED_TOP:
        if k not in obj:
            errs.append(f"missing top-level {k}")
    if obj.get("intent") not in ("normal", "style_requested"):
        errs.append("intent must be normal/style_requested")
    for u in obj.get("units", []):
        for k in REQUIRED_UNIT:
            if k not in u:
                errs.append(f"unit {u.get('uid')} missing {k}")
        if u.get("label") not in ("删", "压", "留"):
            errs.append(f"unit {u.get('uid')} bad label {u.get('label')}")
        if u.get("type") == "code" and u.get("label") == "压":
            errs.append(f"unit {u.get('uid')} code 不可压（仅删/留）")
    return errs
