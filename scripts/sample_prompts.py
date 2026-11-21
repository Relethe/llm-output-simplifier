"""阶段 2 抽样：LMSYS(dev) + WildChat(test) → data/prompts_dev.jsonl / prompts_test.jsonl 各 100。

流程（SPEC v0.2 §6）：流式读取 → 取首轮用户提问 → 廉价筛选（长度 10–2000 / 毒性标记 / redacted / 纯问候）
→ 归一化去重 → G1(glm-5.3) 预分类四类（创作/有害/PII/实时/问候/无关 → 排除）→ 配额（每类 25，中文≥8）
→ 写 jsonl（id/source/source_id/lang/category/text）+ 抽 40 条供用户亲手抽查（T2.2）。

运行：.venv\\Scripts\\python.exe -m scripts.sample_prompts [--max-scan 15000] [--max-classify 900]
证据类型：抽样为程序实测；分类为 AI 代理（G1），待用户抽查校准。
"""
import os
import sys
import json
import re
import random
import hashlib
import argparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HOME"] = os.path.join(ROOT, "data", "hf-cache")
os.environ["HF_DATASETS_CACHE"] = os.path.join(ROOT, "data", "hf-cache", "datasets")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(ROOT, ".env"))
from scripts.llm_client import LLMClient, load_config  # noqa: E402

CATEGORIES = ["问答", "代码", "解释", "建议"]
GREETINGS = {"hi", "hello", "hey", "hi there", "hello there", "hey there", "你好", "您好", "嗨"}

CLASSIFY_SYS = (
    "你是文本分类器。把用户提问归入且仅归入一类，只输出一个词（问答/代码/解释/建议/排除），不要解释。\n"
    "类别判定：\n"
    "- 代码：明确要求编写/生成/修改/调试代码、程序、脚本、工具（如“写一个函数”“帮我做个程序”“debug”“做一个…系统/专家”）。\n"
    "- 问答：索取事实信息——定义、具体事实、公式、表达式、规则、方法步骤、“怎么做/如何配置/有哪些”的事实性提问。"
    "即使涉及技术（如 wifi 连接方式、DAX 表达式、WAF 规则、游戏配置），只要在问事实/方法而非要你写代码，归问答。"
    "“最…的是什么”类事实/观点提问也归问答。\n"
    "- 解释：要求深入讲解概念、原理、机制、为什么（如“解释相对论”“为什么天空是蓝的”“提取技术特征并说明”）。\n"
    "- 建议：征求推荐、决策、做法建议（如“我该选哪个”“推荐什么”“怎么做更好”“有哪些好的做法”）。\n"
    "- 排除：创作/角色扮演、有害、含个人信息、需实时信息（天气/股价/新闻）、纯问候、与四类无关。\n"
    "关键区分：问事实/方法=问答；要你写代码=代码；讲原理=解释；给推荐/决策=建议。"
)


def first_user_text(conversation):
    for t in conversation or []:
        if t.get("role") == "user" and isinstance(t.get("content"), str):
            return t["content"]
    return None


def cheap_filter(text, flagged=False, toxic=False, redacted=False):
    if not text:
        return False
    n = len(text)
    if n < 10 or n > 2000:
        return False
    if flagged or toxic or redacted:
        return False
    if text.strip().lower() in GREETINGS:
        return False
    return True


def normalize(text):
    t = re.sub(r"[^\w\s]", "", text.lower(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", t).strip()


def is_chinese(lang, text):
    if lang and "chinese" in str(lang).lower():
        return True
    if not text:
        return False
    cjk = sum(1 for ch in text if "一" <= ch <= "鿿")
    return cjk / max(len(text), 1) > 0.3


def select_quota(items, per_cat=25, min_zh=8, seed=42):
    rng = random.Random(seed)
    by_cat = {c: [] for c in CATEGORIES}
    for it in items:
        if it.get("category") in by_cat:
            by_cat[it["category"]].append(it)
    selected, stats = [], {}
    for c in CATEGORIES:
        pool = by_cat[c][:]
        rng.shuffle(pool)
        zh = [x for x in pool if x.get("zh")]
        non = [x for x in pool if not x.get("zh")]
        pick = zh[:min_zh]
        rest = zh[min_zh:] + non
        rng.shuffle(rest)
        pick += rest[:max(0, per_cat - len(pick))]
        selected += pick
        z = sum(1 for x in pick if x.get("zh"))
        stats[c] = {"count": len(pick), "zh": z,
                    "zh_shortfall": z < min_zh, "count_shortfall": len(pick) < per_cat}
    return selected, stats


def classify_prompt(client, text):
    # glm-5.3 此部署强制推理：用 reasoning.effort=low 压开销 + temperature=0 保确定性（见日志第7条）
    res = client.call("g1", [{"role": "system", "content": CLASSIFY_SYS},
                             {"role": "user", "content": text[:2000]}],
                      reasoning={"effort": "low"}, temperature=0)
    out = (res["text"] or "").strip()
    for c in CATEGORIES + ["排除"]:
        if c in out:
            return c
    return "排除"


def stream_candidates(name, source, max_scan, exclude_hashes=None):
    from datasets import load_dataset  # 懒加载，便于纯逻辑单测
    exclude_hashes = exclude_hashes or set()
    ds = load_dataset(name, split="train", streaming=True)
    seen = set()
    n = 0
    for row in ds:
        n += 1
        if n > max_scan:
            break
        text = first_user_text(row.get("conversation"))
        if not text:
            continue
        om = row.get("openai_moderation") or []
        flagged = bool(om and om[0].get("flagged"))
        toxic = bool(row.get("toxic"))
        redacted = bool(row.get("redacted"))
        if not cheap_filter(text, flagged, toxic, redacted):
            continue
        h = hashlib.md5(normalize(text).encode("utf-8")).hexdigest()
        if h in seen or h in exclude_hashes:
            continue
        seen.add(h)
        lang = row.get("language")
        sid = row.get("conversation_id") or row.get("conversation_hash")
        yield {"text": text, "lang": lang, "zh": is_chinese(lang, text),
               "source": source, "source_id": sid, "norm_hash": h}


def _write_ckpt(path, items):
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def build_set(client, name, source, out_path, max_scan, max_classify, seed=42, exclude_hashes=None):
    # 断点续跑 + 两阶段中文优先：
    #   A 廉价扫描收集候选（不调 API），按中文/非中文分池；
    #   B1 优先分类中文填 ≥min_zh/类（中文稀疏，直击稀缺资源）；B2 非中文补到 25/类。
    ckpt = os.path.join(ROOT, "data", f"_ckpt_{source}.jsonl")
    prev = []
    if os.path.exists(ckpt):
        with open(ckpt, encoding="utf-8") as f:
            prev = [json.loads(line) for line in f if line.strip()]
    done_hashes = {x["norm_hash"] for x in prev} | set(exclude_hashes or set())
    classified = [x for x in prev if x.get("category") in CATEGORIES]
    resumed = len(prev)
    rng = random.Random(seed)
    zh_pool, non_pool, scanned = [], [], 0
    for cand in stream_candidates(name, source, max_scan, done_hashes):
        scanned += 1
        (zh_pool if cand["zh"] else non_pool).append(cand)
    rng.shuffle(zh_pool)
    rng.shuffle(non_pool)

    def stats_ok(zh_only=False):
        _, st = select_quota(classified, seed=seed)
        if zh_only:
            return all(not s["zh_shortfall"] for s in st.values())
        return all(not s["count_shortfall"] and not s["zh_shortfall"] for s in st.values())

    newly, quota_met = 0, False
    for cand in zh_pool:                      # B1 中文优先
        if newly >= max_classify or stats_ok(zh_only=True):
            break
        cand["category"] = classify_prompt(client, cand["text"])
        newly += 1
        if cand["category"] in CATEGORIES:
            classified.append(cand)
        if newly % 25 == 0:
            _write_ckpt(ckpt, classified)
    for cand in non_pool:                     # B2 非中文补齐
        if newly >= max_classify or quota_met:
            break
        cand["category"] = classify_prompt(client, cand["text"])
        newly += 1
        if cand["category"] in CATEGORIES:
            classified.append(cand)
        if newly % 25 == 0:
            _write_ckpt(ckpt, classified)
        if len(classified) >= 100 and stats_ok():
            quota_met = True
    _write_ckpt(ckpt, classified)
    sel, stats = select_quota(classified, seed=seed)
    for i, it in enumerate(sel):
        it["id"] = f"{source}_{i:03d}"
    with open(out_path, "w", encoding="utf-8") as f:
        for it in sel:
            f.write(json.dumps({k: it[k] for k in ["id", "source", "source_id", "lang", "category", "text"]},
                               ensure_ascii=False) + "\n")
    return sel, stats, {"scanned": scanned, "zh_pool": len(zh_pool), "non_pool": len(non_pool),
                        "newly_classified": newly, "resumed_from": resumed,
                        "classified_total": len(classified), "quota_met": quota_met}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-scan", type=int, default=60000)
    ap.add_argument("--max-classify", type=int, default=600)
    args = ap.parse_args()
    cfg = load_config(os.path.join(ROOT, "config.yaml"))
    client = LLMClient(cfg, phase="dev")
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "human"), exist_ok=True)

    dev_sel, dev_stats, dev_info = build_set(
        client, "lmsys/lmsys-chat-1m", "dev", os.path.join(ROOT, "data", "prompts_dev.jsonl"),
        args.max_scan, args.max_classify)
    dev_hashes = {it["norm_hash"] for it in dev_sel}
    test_sel, test_stats, test_info = build_set(
        client, "allenai/WildChat-1M", "test", os.path.join(ROOT, "data", "prompts_test.jsonl"),
        args.max_scan, args.max_classify, exclude_hashes=dev_hashes)

    rng = random.Random(42)
    spot = rng.sample(dev_sel, min(40, len(dev_sel)))
    with open(os.path.join(ROOT, "human", "classification_spotcheck_40.jsonl"), "w", encoding="utf-8") as f:
        for it in spot:
            f.write(json.dumps({"id": it["id"], "category_g1": it["category"], "lang": it["lang"],
                                "text": it["text"], "user_category": "", "user_correct": ""},
                               ensure_ascii=False) + "\n")

    print("DEV_STATS", json.dumps(dev_stats, ensure_ascii=False))
    print("DEV_INFO", json.dumps(dev_info, ensure_ascii=False))
    print("TEST_STATS", json.dumps(test_stats, ensure_ascii=False))
    print("TEST_INFO", json.dumps(test_info, ensure_ascii=False))
    print("SPENT_CNY", round(client.spent, 4))
    print("SAMPLING_DONE")


if __name__ == "__main__":
    main()
