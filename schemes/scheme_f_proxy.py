"""方案 F LiteLLM proxy 钩子（部署 glue，需 pip install litellm[proxy]）。
调用前：意图分类 + 注入 A（route_request）；强度由请求 metadata.simplify_strength 控制（off/light/full）。
调用后：full 强度可串方案 B（重组见 schemes.scheme_b）；流式句缓冲见 schemes.scheme_f.sentence_buffer。
核心路由逻辑已在 scheme_f.py 单测覆盖；本钩子为部署集成层。
"""
try:
    from litellm.integrations.custom_logger import CustomLogger
    _BASE = CustomLogger
except Exception:  # litellm[proxy] 未安装时降级，便于导入与单测核心逻辑
    _BASE = object

from schemes.scheme_f import route_request  # noqa: E402


class SimplifyProxy(_BASE):
    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        strength = (data.get("metadata") or {}).get("simplify_strength", "light")
        new_msgs, apply_b = route_request(data.get("messages", []), strength)
        data["messages"] = new_msgs
        data.setdefault("metadata", {})["simplify_apply_b"] = apply_b
        return data


proxy_handler = SimplifyProxy()
