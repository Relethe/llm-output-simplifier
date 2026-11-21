"""方案 C：解码参数 logit_bias（SPEC §9.3，低优先级）。
压低常见开场词首 token 概率。仅用于支持 logit_bias 的接口（Chat Completions）；
当前百炼 Responses 端点不支持 logit_bias，故对 dev 模型 N/A——逻辑备妥，适用时启用。
禁止用 max_tokens 截断。encode_fn 须用目标模型自己的分词器。
"""

OPENING_PHRASES = ["Certainly", "As an AI", "Great question", "In summary",
                   "总之", "当然", "首先", "Sure"]


def build_logit_bias(encode_fn, phrases=None, bias=-100):
    """encode_fn(text)->token id 列表；取每个开场词首 token 压 bias。返回 {token_id: bias}。"""
    phrases = phrases if phrases is not None else OPENING_PHRASES
    bias_map = {}
    for p in phrases:
        toks = encode_fn(p)
        if toks:
            bias_map[toks[0]] = bias
    return bias_map
