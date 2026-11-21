"""方案 B 外部简化器（SPEC §9.2）：只输出编辑操作，不自由重写。
当前实际简化模型：gpt-6.2-sol，reasoning effort=low，通过 config.simplifier_external 配置。
改写器看原回答单元+病理表+标注样例，不看必留点/测验题。compress 子集校验由 DeepSeek 裁判做。
"""
import json
import re

from scripts.annotation_prompts import PATHOLOGY_TABLE
from schemes.scheme_b import apply_edits

REWRITE_SYS = (
    "你是保守精简改写器。对给定单元只输出编辑操作 JSON 数组，禁止自由重写整篇。"
    "操作：delete(删整单元)/keep(保留)/compress(压缩，text 为压缩后文本)/move_first(移到开头，最多 1 次)。"
    "代码块(type=code)只能 keep 或 delete。compress 后信息必须是原单元信息的子集，不得新增或矛盾。\n"
    "【保守口径——最高优先级】默认 keep。宁可少删，绝不丢信息。"
    "只有当单元是纯套话——复述问题开场、AI身份免责、路标预告、空洞平衡收尾、未请求说教、结尾复述——"
    "且不含任何事实/步骤/数字/条件/示例/解释时，才可 delete。"
    "只要单元含任何实质内容（哪怕一句有用信息），一律 keep 或 compress；compress 必须保留全部信息点，只去掉冗余措辞。"
    "拿不准的一律 keep。把直接回答单元 move_first 到开头。\n"
    "只输出 JSON 数组，例如 [{\"uid\":1,\"op\":\"keep\"},{\"uid\":2,\"op\":\"delete\"}]。\n"
    "病理表（仅用于识别纯套话，含实质内容者不适用 delete）：\n"
    + "\n".join(f"{c} {n}：{d}（{t}）" for c, n, d, t in PATHOLOGY_TABLE)
)


def build_rewrite_messages(units, examples_text=""):
    slim = [{"uid": u["uid"], "type": u["type"], "text": u["text"]} for u in units]
    sys_prompt = REWRITE_SYS
    if examples_text:
        sys_prompt += "\n标注样例（仅参考风格，勿照抄内容）：\n" + examples_text
    user = "待编辑单元（JSON）：\n" + json.dumps(slim, ensure_ascii=False)
    return [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user}]


def parse_edit_ops(text):
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        s, e = text.find("["), text.rfind("]")
        if s >= 0 and e > s:
            text = text[s:e + 1]
    return json.loads(text)


def compress_is_subset(client, original, compressed):
    """裁判校验：压缩版信息点 ⊆ 原单元信息点。通过返回 True，否则回退 keep。"""
    msgs = [{"role": "system", "content": "判断压缩版的信息是否都是原版信息的子集（无新增、无矛盾）。只回答 是 或 否。"},
            {"role": "user", "content": f"原版：{original}\n压缩版：{compressed}"}]
    res = client.call("judge", msgs, reasoning={"effort": "low"}, temperature=0)
    return res["text"].strip().startswith("是")


def apply_scheme_B(client, units, disable=None, examples_text="", return_details=False,
                   simplifier_role="simplifier_external"):
    """方案 B 完整流程：指定简化器生成 edit ops→禁用项 keep→DeepSeek compress 子集校验→确定性重组。
    默认使用 Astra。return_details=True 时返回 text/ops/simplifier_meta。"""
    disable = disable or []
    msgs = build_rewrite_messages(units, examples_text)
    res = client.call(simplifier_role, msgs, reasoning={"effort": "low"}, temperature=0, max_wall_s=180)
    ops = parse_edit_ops(res["text"])
    by_uid = {u["uid"]: u for u in units}
    for op in ops:
        if op.get("op") in disable:
            op["op"] = "keep"
    for op in ops:
        if op.get("op") == "compress" and op.get("uid") in by_uid:
            if not compress_is_subset(client, by_uid[op["uid"]]["text"], op.get("text", "")):
                op["op"] = "keep"
    text, sanitized = apply_edits(units, ops)
    if not text.strip():
        # 安全回退：简化器误删全部单元时保留原文，避免保留率=0
        text = "\n".join(u["text"] for u in units)
        sanitized = list(sanitized) + ["empty_fallback_to_original"]
    if return_details:
        return {"text": text, "ops": ops, "sanitized_uids": sanitized, "simplifier_meta": res["meta"]}
    return text
