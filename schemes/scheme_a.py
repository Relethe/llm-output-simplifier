"""方案 A：输入侧系统提示词（SPEC v0.2 §9.1）+ 基线 + 逐条消融接口。
RULES 为 13 条规则；消融去掉规则 1–11 中的某条（remove=k）。基线仅「请简洁回答。」。
"""

RULES = [
    "1. 第一句直接给出答案或结论；如果答案取决于条件，先给最常见情况下的结论，再说明会改变结论的那个条件。[P8]",
    "2. 不复述或改写用户的问题，不评价问题本身。[P1]",
    "3. 除非用户问起，不提及自己是 AI。[P2]",
    "4. 不写“下面介绍……”之类的预告句，直接给内容。[P3]",
    "5. 给出代码后，不逐行用文字复述代码，只解释不显而易见的部分。[P4]",
    "6. 只讲回答问题所需的背景。[P5]",
    "7. 不加用户没要求的劝告或道德评论。[P7]",
    "8. 不用“各有道理”“取决于你”收尾；确实取决于条件时，说出是哪个条件。[P6]",
    "9. 示例只给用户要求的数量；没有要求时最多给一个。[P9]",
    "10. 结尾不复述前文。[P10]",
    "11. 只在能帮助快速查找时才用列表、标题和加粗。[P11]",
    "12. 不得省略回答问题所需的步骤、条件、数字和警告。",
    "13. 用户明确要求某种风格或篇幅时，以用户要求为准，以上规则只保留第 1 和第 12 条。",
]
BASELINE_PROMPT = "请简洁回答。"


def build_prompt(remove=None):
    rules = [r for r in RULES if not (remove is not None and r.startswith(f"{remove}."))]
    return "回答时遵守以下规则：\n" + "\n".join(rules) + "\n用用户使用的语言回答。"


SCHEME_A_PROMPT = build_prompt()


def build_messages(user_text, mode="A", remove=None):
    """mode: 'A'（方案A，可 remove 消融）/ 'baseline'（请简洁回答）/ 'off'（无系统提示）。"""
    if mode == "off":
        return [{"role": "user", "content": user_text}]
    if mode == "baseline":
        sys_prompt = BASELINE_PROMPT
    else:
        sys_prompt = build_prompt(remove=remove)
    return [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_text}]
