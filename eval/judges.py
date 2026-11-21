"""阶段 6 裁判（SPEC §10.2）：保留率逐点、新增错误、成对盲评（固定问题+正反序）。
裁判=GLM 独立会话，文本去来源标签。盲评不问“哪个更好”。所有结果属 AI 代理评测，待人工校准。
"""
import json
import re

BLIND_QUESTION = "哪个让你更快拿到需要的信息，而且不缺东西？"


def _parse_array(text):
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        s, e = text.find("["), text.rfind("]")
        if s >= 0 and e > s:
            text = text[s:e + 1]
    try:
        return json.loads(text)
    except Exception:
        return []


def retention_judge(client, point, simplified):
    """必留点在简化版中是否仍成立（部分成立按不成立）。"""
    msgs = [{"role": "system", "content": "判断必留点在简化版中是否仍成立。部分成立按不成立。只回答 是 或 否。"},
            {"role": "user", "content": f"必留点：{point}\n简化版：{simplified}"}]
    res = client.call("judge", msgs, reasoning={"effort": "low"}, temperature=0)
    return res["text"].strip().startswith("是")


def new_errors_judge(client, original, simplified):
    """列出简化版中原回答不支持或矛盾的说法（JSON 数组）。"""
    msgs = [{"role": "system", "content": "列出简化版中原回答不支持或与之矛盾的说法，输出 JSON 数组（每项一条说法）；没有则 []。只输出 JSON。"},
            {"role": "user", "content": f"原回答：{original}\n简化版：{simplified}"}]
    res = client.call("judge", msgs, reasoning={"effort": "low"}, temperature=0)
    return _parse_array(res["text"])


def _judge_once(client, left, right):
    msgs = [{"role": "system", "content": f"比较两份回答。问题固定：{BLIND_QUESTION} 只回答 A（左）/B（右）/一样。不得评判“哪个更好”。"},
            {"role": "user", "content": f"左：{left}\n右：{right}"}]
    res = client.call("judge", msgs, reasoning={"effort": "low"}, temperature=0)
    t = res["text"].strip()
    if t.startswith("A"):
        return "A"
    if t.startswith("B"):
        return "B"
    return "一样"


def blind_eval(client, text_a, text_b):
    """正反序各判一次，不一致记“一样”。返回 'A'/'B'/'一样'（A=text_a 胜）。"""
    r1 = _judge_once(client, text_a, text_b)          # A 左 B 右
    r2 = _judge_once(client, text_b, text_a)          # B 左 A 右
    r2_mapped = {"A": "B", "B": "A", "一样": "一样"}[r2]
    return r1 if r1 == r2_mapped else "一样"
