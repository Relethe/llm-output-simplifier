"""阶段 7.3 AI 读者测验（SPEC §11.3）。证据类型：AI 代理评测。
出题 GLM 只看必留点（不看简化版）；答题 GLM 三条件独立会话（原版/简化版/无文本），
指令“只依据给定文本，找不到答找不到”。剔除无文本也能答对的题（测的是模型知识非文本）；
剔除后 <60 题补出题。通过：简化版正确率比原版降 ≤3 个百分点。
"""
import json
import re

QUESTION_SYS = ("你是出题员。只依据给定的必留点出 2–3 道理解题，附标准答案。不得参考任何简化版。"
                "题目应能由必留点回答。只输出 JSON 数组 [{\"q\":\"...\",\"a\":\"...\"}]。")
ANSWER_SYS = ("只依据给定文本回答问题；文本里找不到就回答“找不到”。不要使用你自己的知识。"
              "逐题作答，只输出 JSON 数组 [{\"q\":\"...\",\"answer\":\"...\"}]。")


def build_question_writer_messages(points):
    return [{"role": "system", "content": QUESTION_SYS},
            {"role": "user", "content": "必留点：\n" + json.dumps(points, ensure_ascii=False)}]


def build_answerer_messages(text, questions):
    prefix = ("文本：\n" + text + "\n\n") if text else "（无文本）\n\n"
    return [{"role": "system", "content": ANSWER_SYS},
            {"role": "user", "content": prefix + "问题：\n" + json.dumps(questions, ensure_ascii=False)}]


def _norm(s):
    return re.sub(r"\s+", "", str(s).lower().strip())


def grade_answer(answer, standard):
    a, s = _norm(answer), _norm(standard)
    if not a or a == "找不到":
        return False
    return a == s or s in a or a in s


def accuracy(graded):
    return sum(1 for g in graded if g) / len(graded) if graded else 0.0


def filter_by_no_text(items):
    """items 含 no_text_correct；保留无文本答错的题（剔除靠模型知识就能答对的）。"""
    return [it for it in items if not it.get("no_text_correct")]


def reader_test_pass(acc_orig, acc_simp, threshold_pp=3.0):
    return (acc_orig - acc_simp) * 100 <= threshold_pp
