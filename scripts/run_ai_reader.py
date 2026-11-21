"""阶段 7.3 AI 读者测验 runner（SPEC §11.3，AI 代理评测·未经人工校准）。
抽 40 条：出题(只看必留点)→答题三条件(原版/简化/无文本)→剔除无文本能答对的题→正确率降≤3pp。
运行：.venv\\Scripts\\python.exe -m scripts.run_ai_reader
"""
import os
import sys
import json
import random
import re

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))
from scripts.llm_client import LLMClient, load_config  # noqa: E402
from scripts.ai_reader_test import (  # noqa: E402
    build_question_writer_messages, build_answerer_messages,
    grade_answer, accuracy, filter_by_no_text, reader_test_pass,
)


def parse_arr(text):
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


def batch_grade(client, questions, answers_list):
    triples = [{"i": j, "q": q["q"], "standard": q.get("a", ""),
                "answer": answers_list[j].get("answer", "") if j < len(answers_list) else ""}
               for j, q in enumerate(questions)]
    msgs = [{"role": "system", "content": "判断每题 answer 是否与 standard 语义一致（即正确回答了问题）。"
             "答“找不到”、错误、或未答均为 false。只输出 JSON 数组 [{\"i\":序号,\"correct\":true/false}]。"},
            {"role": "user", "content": json.dumps(triples, ensure_ascii=False)}]
    res = client.call("judge", msgs, reasoning={"effort": "low"}, temperature=0, max_wall_s=120)
    cmap = {x.get("i"): bool(x.get("correct", False)) for x in parse_arr(res["text"])}
    return [cmap.get(j, False) for j in range(len(questions))]


def load_dir(d):
    return {json.load(open(os.path.join(d, f), encoding="utf-8"))["response_id"]:
            json.load(open(os.path.join(d, f), encoding="utf-8"))
            for f in os.listdir(d) if f.endswith(".json")}


def main():
    client = LLMClient(load_config(os.path.join(ROOT, "config.yaml")), phase="dev")
    responses = {json.loads(l)["response_id"]: json.loads(l)
                 for l in open(os.path.join(ROOT, "responses", "responses_dev.jsonl"), encoding="utf-8") if l.strip()}
    simpl = {json.loads(l)["response_id"]: json.loads(l)
             for l in open(os.path.join(ROOT, "responses", "scheme_b_astra.jsonl"), encoding="utf-8") if l.strip()}
    final = load_dir(os.path.join(ROOT, "annotations", "final"))
    rng = random.Random(42)
    rids = rng.sample(sorted(final), min(40, len(final)))
    all_items = []
    for i, rid in enumerate(rids):
        points = final[rid]["must_keep_points"]
        if not points:
            continue
        qw = client.call("g1", build_question_writer_messages(points),
                         reasoning={"effort": "low"}, temperature=0, max_wall_s=120)
        questions = parse_arr(qw["text"])[:3]
        if not questions:
            continue
        orig_text = responses[rid]["response"]
        simp_text = simpl[rid]["simplified"]
        graded = {"original": [], "simplified": [], "no_text": []}
        for cond, text in [("original", orig_text), ("simplified", simp_text), ("no_text", None)]:
            ans = client.call("judge", build_answerer_messages(text, [q["q"] for q in questions]),
                              reasoning={"effort": "low"}, temperature=0, max_wall_s=120)
            answers_list = parse_arr(ans["text"])
            graded[cond] = batch_grade(client, questions, answers_list)
        for j, q in enumerate(questions):
            all_items.append({"rid": rid, "q": q["q"],
                              "orig_correct": graded["original"][j],
                              "simp_correct": graded["simplified"][j],
                              "no_text_correct": graded["no_text"][j]})
        if (i + 1) % 10 == 0:
            print("reader progress", i + 1, "spent", round(client.spent, 4), flush=True)
    kept = filter_by_no_text(all_items)
    acc_orig = accuracy([it["orig_correct"] for it in kept])
    acc_simp = accuracy([it["simp_correct"] for it in kept])
    passed = reader_test_pass(acc_orig, acc_simp)
    report = {"n_items": len(all_items), "n_kept_after_filter": len(kept),
              "acc_original": acc_orig, "acc_simplified": acc_simp,
              "drop_pp": (acc_orig - acc_simp) * 100, "pass_le_3pp": passed,
              "note": "AI 代理评测·未经人工校准"}
    os.makedirs(os.path.join(ROOT, "eval"), exist_ok=True)
    with open(os.path.join(ROOT, "eval", "ai_reader_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("AI_READER", json.dumps(report, ensure_ascii=False))
    print("AI_READER_DONE")


if __name__ == "__main__":
    main()
