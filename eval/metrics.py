"""阶段 6 阅读时间指标（SPEC v0.2 §1.1/1.2）。
T_总 = Σ(L_i / v_类型(i)) + c·N_结构；T_答 = 读到首个直接回答单元(answer_uid)的预估时间。
L_i：英文词数 / 中文字数(CJK) / 代码行数 / 表格行·列表项各计 1。v 来自 reading_speed.json。
N_结构：标题/列表/表格/代码/正文 类别相邻切换次数。c 单位秒/切换。结果单位：秒。
中文正文 v 未标定(null)时暂用英文值占位（推断），用户阶段7实测后重算。
"""


def _cjk(text):
    return sum(1 for ch in text if "一" <= ch <= "鿿")


def is_chinese(text):
    return _cjk(text) / max(len(text), 1) > 0.3


def unit_length(u):
    t = u["type"]
    text = u["text"]
    if t == "code":
        return max(1, text.count("\n") + 1)
    if t in ("table_row", "list_item"):
        return 1
    if is_chinese(text):
        return max(1, _cjk(text))
    return max(1, len(text.split()))


def speed_for(u, speeds):
    t = u["type"]
    if t == "code":
        return speeds["code"]["value"]
    if t == "table_row":
        return speeds["table_row"]["value"]
    if t == "list_item":
        return speeds["list_item"]["value"]
    if is_chinese(u["text"]):
        v = speeds["chinese_text"]["value"]
        return v if v else speeds["english_text"]["value"]  # interim 占位（推断）
    return speeds["english_text"]["value"]


def struct_cat(u):
    return {"heading": "heading", "list_item": "list",
            "table_row": "table", "code": "code"}.get(u["type"], "text")


def structure_switches(units):
    cats = [struct_cat(u) for u in units]
    return sum(1 for i in range(1, len(cats)) if cats[i] != cats[i - 1])


def t_total(units, speeds, c):
    minutes = sum(unit_length(u) / speed_for(u, speeds) for u in units)
    return minutes * 60 + c * structure_switches(units)


def t_answer(units, speeds, c, answer_uid):
    secs = 0.0
    cats = []
    for u in units:
        secs += unit_length(u) / speed_for(u, speeds) * 60
        cats.append(struct_cat(u))
        if u["uid"] == answer_uid:
            break
    sw = sum(1 for i in range(1, len(cats)) if cats[i] != cats[i - 1])
    return secs + c * sw
