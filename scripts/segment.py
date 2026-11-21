"""单元切分（SPEC v0.2 §8.1）：正文按句、列表项/表格行/标题各 1 单元、整个代码块 1 单元(type=code)。
代码块逐字节保留（方案 B 硬约束）。中文按 。！？；+换行分句；英文用 pysbd。
"""
import re

import pysbd

_FENCE = re.compile(r"^\s*(```|~~~)")
_HEADING = re.compile(r"^\s*#{1,6}\s")
_TABLE = re.compile(r"^\s*\|.*\|\s*$")
_LIST = re.compile(r"^\s*([-*+]|\d+\.)\s")
_EN_SEG = pysbd.Segmenter(language="en", clean=False)


def _is_chinese(text):
    cjk = sum(1 for ch in text if "一" <= ch <= "鿿")
    return cjk / max(len(text), 1) > 0.3


def split_sentences(text):
    if _is_chinese(text):
        out = []
        for part in re.split(r"(?<=[。！？；])", text):
            for seg in part.split("\n"):
                seg = seg.strip()
                if seg:
                    out.append(seg)
        return out
    return [s.strip() for s in _EN_SEG.segment(text) if s.strip()]


def segment(text):
    units = []
    lines = text.split("\n")
    para = []

    def flush_para():
        nonlocal para
        if para:
            ptext = "\n".join(para).strip()
            if ptext:
                for s in split_sentences(ptext):
                    units.append({"type": "text", "text": s})
            para = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if _FENCE.match(line):
            flush_para()
            fence = line.strip()[:3]
            code_lines = [line]
            i += 1
            while i < len(lines):
                code_lines.append(lines[i])
                closed = lines[i].strip().startswith(fence)
                i += 1
                if closed:
                    break
            units.append({"type": "code", "text": "\n".join(code_lines)})
            continue
        if _HEADING.match(line):
            flush_para()
            units.append({"type": "heading", "text": line.strip()})
            i += 1
            continue
        if _TABLE.match(line):
            flush_para()
            units.append({"type": "table_row", "text": line.strip()})
            i += 1
            continue
        if _LIST.match(line):
            flush_para()
            units.append({"type": "list_item", "text": line.strip()})
            i += 1
            continue
        if line.strip() == "":
            flush_para()
            i += 1
            continue
        para.append(line)
        i += 1
    flush_para()
    for uid, u in enumerate(units, 1):
        u["uid"] = uid
    return units
