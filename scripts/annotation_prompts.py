"""阶段 4 G1/G2 标注 prompt（SPEC v0.2 §8.2/8.3/8.4）+ JSON 解析。
G1/G2 同模型(glm-5.3)独立会话；G2 规范措辞改写、病理表顺序打乱（§2 隔离）。
"""
import json
import re
import random

PATHOLOGY_TABLE = [
    ("P1", "复述问题式开场", "开头复述、改写或评价用户的问题", "删"),
    ("P2", "AI 身份免责", "没被问到却声明自己是 AI、没有观点", "删"),
    ("P3", "路标句", "预告接下来讲什么，本身无信息", "删"),
    ("P4", "复述代码", "用文字逐行复述刚写出的代码", "压"),
    ("P5", "未请求的背景", "用户没问、也不影响理解答案的背景", "压或删"),
    ("P6", "空洞平衡收尾", "说“各有道理”“取决于你”，却不说取决于什么", "删"),
    ("P7", "未请求的说教", "没被要求的劝告、道德评论、呼吁", "删"),
    ("P8", "答案后置", "直接答案不在开头", "留，加 move_first"),
    ("P9", "多余示例或扩展", "超出需要的第二、第三个示例或延伸话题", "压"),
    ("P10", "结尾总结复述", "结尾重复前文", "删"),
    ("P11", "格式膨胀", "过度加粗、一句一条的列表、不必要的标题", "压"),
]

_SCHEMA = ('{"response_id":"...","annotator":"G1","intent":"normal","correctness_issue":null,'
           '"must_keep_points":[{"pid":1,"text":"..."}],'
           '"units":[{"uid":1,"label":"删","move_first":false,"pathology":["P1"],"note":""}]}')


def _pathology_text(variant):
    rows = list(PATHOLOGY_TABLE)
    if variant == "G2":
        random.Random(42).shuffle(rows)  # G2 样例顺序打乱
    return "\n".join(f"{c} {name}：{defn}（倾向：{tend}）" for c, name, defn, tend in rows)


def build_system_prompt(variant="G1"):
    if variant == "G2":
        intro = ("你是独立标注员 G2。请依据下述规范对回答做标注，仅输出一个 JSON 对象，勿输出任何解释。"
                 "判断口径：label 删=移除不伤必留点；压=含必留点但可压缩到原长六成以下；留=其他。"
                 "代码块仅可删或留。直接回答若不在开头则 move_first=true。")
    else:
        intro = ("你是标注员 G1。按规范标注给定回答，只输出 JSON，不要解释。"
                 "label：删=去掉不影响任何必留点；压=含必留点但能用不到原长 60% 表达；留=其余。"
                 "代码块(type=code)只能标 删 或 留。直接回答但不在开头 → move_first=true。")
    return (
        intro + "\n"
        "【保守口径】默认保留(留)。仅当单元是纯冗余套话——复述问题开场(P1)、AI身份免责(P2)、路标预告(P3)、"
        "空洞平衡收尾(P6)、未请求说教(P7)、结尾复述(P10)——且不含任何实质信息时才标删。"
        "含实质内容（步骤/条件/数字/解释/示例）一律留或压。拿不准一律留。宁可少删，不可误删实质信息。\n"
        "回答级：intent=normal/style_requested（用户明确要求风格或篇幅为后者，其修辞不计病症）；"
        "correctness_issue=原回答本身有错的说明，否则 null；"
        "must_keep_points=把原回答拆成原子信息点、标出提问者需要知道的 [{\"pid\":1,\"text\":...}]。\n"
        "单元级：对每个已编 uid 的单元给 label/move_first/pathology/note。"
        "**单元只输出 uid/label/move_first/pathology/note，勿重复 text/type（切分已提供，重复会浪费）。**\n"
        "病理表：\n" + _pathology_text(variant) + "\n"
        "输出 JSON 格式：\n" + _SCHEMA
    )


def build_annotation_messages(response_id, question, units, variant="G1"):
    slim = [{"uid": u["uid"], "type": u["type"], "text": u["text"]} for u in units]
    user = (f"response_id: {response_id}\n用户提问：{question}\n"
            f"待标注单元（JSON）：\n{json.dumps(slim, ensure_ascii=False)}")
    return [{"role": "system", "content": build_system_prompt(variant)},
            {"role": "user", "content": user}]


def parse_annotation_json(text):
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        s, e = text.find("{"), text.rfind("}")
        if s >= 0 and e > s:
            text = text[s:e + 1]
    return json.loads(text)
