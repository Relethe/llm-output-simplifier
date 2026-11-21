"""方案 B 核心：编辑操作确定性重组（SPEC v0.2 §9.2）。
改写模型只输出 edit ops（delete/move_first/compress/keep），程序确定性重组，不允许自由重写。
硬约束：type=code 仅 keep/delete；move_first 最多 1 次；违规操作确定性sanitize为 keep。
compress 的信息点子集校验由裁判做（见 validate_compress，I/O），此处只做确定性重组。
"""


def apply_edits(units, edits):
    """返回 (重组文本, sanitized_uid列表)。sanitize：code 的非 keep/delete、超额的 move_first → keep。"""
    by_uid = {u["uid"]: u for u in units}
    emap = {e["uid"]: e for e in edits}
    ops = {}
    sanitized = []
    mf_count = 0
    for u in units:
        e = emap.get(u["uid"], {"op": "keep"})
        op = e.get("op", "keep")
        if u["type"] == "code" and op not in ("keep", "delete"):
            op = "keep"
            sanitized.append(u["uid"])
        if op == "move_first":
            mf_count += 1
            if mf_count > 1:
                op = "keep"
                sanitized.append(u["uid"])
        if op not in ("keep", "delete", "move_first", "compress"):
            op = "keep"
            sanitized.append(u["uid"])
        ops[u["uid"]] = (op, e.get("text"))
    mf_uids = [uid for uid, (op, _) in ops.items() if op == "move_first"]
    ordered = list(mf_uids)
    for u in units:
        uid = u["uid"]
        if ops[uid][0] in ("delete", "move_first"):
            continue
        ordered.append(uid)
    parts = []
    for uid in ordered:
        u = by_uid[uid]
        op, ctext = ops[uid]
        if op == "compress" and ctext is not None:
            parts.append(ctext)
        else:
            parts.append(u["text"])
    return "\n\n".join(parts), sanitized
