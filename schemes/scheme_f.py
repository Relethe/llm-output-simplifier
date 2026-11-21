"""方案 F：代理网关核心逻辑（SPEC §9.4）。
调用前意图分类（创作/风格→放行，其余注入方案A）；强度 off/light/full；流式按句缓冲。
核心纯逻辑可单测；LiteLLM proxy 部署 glue 见 scheme_f_proxy.py（需 litellm[proxy]）。
"""
import re

from schemes.scheme_a import build_messages

CREATIVE_KW = ["写诗", "故事", "小说", "角色扮演", "有趣", "写成", "幽默", "散文", "剧本",
               "roleplay", "story", "poem", "funny", "creative", "写得"]
CODE_KW = ["代码", "函数", "编程", "program", "code", "debug", "脚本", "script", "报错"]


_CREATIVE_RE = re.compile(r"(写|创作|编|作).{0,12}(诗|故事|小说|散文|剧本|歌|段子)")


def intent_classify(text):
    t = text.lower()
    if _CREATIVE_RE.search(t) or any(k in t for k in CREATIVE_KW):
        return "creative_style"
    if any(k in t for k in CODE_KW):
        return "code"
    return "other"


def route_request(messages, strength="off"):
    """返回 (新messages, 是否后置B)。off 不动；创作/风格放行；light 注入A；full 注入A+后置B。"""
    if strength == "off":
        return messages, False
    user_text = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    if intent_classify(user_text) == "creative_style":
        return messages, False  # 创作/风格直接放行，不误伤
    new_msgs = build_messages(user_text, mode="A")
    return new_msgs, (strength == "full")


_SENT_END = re.compile(r"[。！？；.!?]")


def sentence_buffer(tokens):
    """把 token 流缓冲成整句yield（句末 。！？；.!?）；末尾残余也yield。用于流式B降首字延迟波动。"""
    buf = ""
    for tok in tokens:
        buf += tok
        while True:
            m = _SENT_END.search(buf)
            if not m:
                break
            idx = m.end()
            yield buf[:idx]
            buf = buf[idx:]
    if buf.strip():
        yield buf
