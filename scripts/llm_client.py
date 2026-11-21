"""统一 OpenAI 兼容模型客户端 + 调用日志 + 预算熔断 + 留出锁。

所有 provider（DeepSeek / DashScope / GLM / Moonshot）都走 OpenAI 兼容接口。
密钥从 .env 读（config 只存环境变量名，不落明文）。
每次调用记录 model / version / params / timestamp / tokens / latency / cost（SPEC §3）。
"""
import json
import os
import time
from datetime import datetime, timezone
from types import SimpleNamespace

import yaml
from dotenv import load_dotenv
from openai import (
    OpenAI, APIConnectionError, APITimeoutError, RateLimitError, InternalServerError,
)

# 瞬时错误（网络瞬断/超时/限流/5xx）→ 退避重试；认证/参数错误不重试
TRANSIENT = (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)


class HoldoutLockedError(RuntimeError):
    """留出模型在开发阶段被调用（SPEC：开发期间一律不调用）。"""


class BudgetExceededError(RuntimeError):
    """累计花费已达预算上限，硬性熔断。"""


def load_config(path="config.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class LLMClient:
    def __init__(self, config, phase="dev", log_path="logs/calls.jsonl",
                 budget_path="logs/budget_state.json", env_file=".env"):
        if env_file:
            load_dotenv(env_file)
        self.config = config
        self.phase = phase
        self.log_path = log_path
        self.budget_path = budget_path
        self.cap = config.get("budget", {}).get("cap_cny")
        self.pricing = config.get("pricing_cny_per_mtok", {})
        self.spent = self._load_spent()
        self._specs = self._build_specs()
        self._clients = {}

    def _load_spent(self):
        if os.path.exists(self.budget_path):
            with open(self.budget_path, encoding="utf-8") as f:
                return float(json.load(f).get("spent_cny", 0.0))
        return float(self.config.get("budget", {}).get("spent_cny", 0.0))

    def _build_specs(self):
        m = self.config["models"]
        specs = {d["role"]: d for d in m["dev"]}
        for role, spec in m.items():
            if role != "dev" and isinstance(spec, dict) and "model" in spec:
                specs[role] = spec
        return specs

    def _get_client(self, role):
        if role not in self._clients:
            spec = self._specs[role]
            key = os.environ.get(spec["api_key_env"]) or "missing-key"
            # timeout=300 容纳长代码生成（实测画小猪 8647token/39.5s，qwen 旗舰更长）；
            # max_retries=2 避免与外层退避重试嵌套放大空转
            self._clients[role] = OpenAI(base_url=spec["base_url"], api_key=key,
                                         max_retries=2, timeout=300)
        return self._clients[role]

    def _invoke(self, client, model, messages, params, protocol="chat", max_wall_s=None):
        """真实 API 调用；单元测试 monkeypatch 此方法以避免费用。
        protocol="responses" 走 OpenAI Responses API（百炼 token-plan 端点）；否则 Chat Completions。"""
        if protocol == "responses":
            # 流式：长回答逐 token 到达，避免非流式总时长超时（实测 qwen 长代码 >300s 卡死）
            kwargs = {"model": model, "input": messages, "stream": True}
            for k, v in params.items():
                if v is None:
                    continue
                if k == "max_tokens":
                    k = "max_output_tokens"
                kwargs[k] = v
            text_parts = []
            final = None
            t_start = time.perf_counter()
            for event in client.responses.create(**kwargs):
                if max_wall_s is not None and (time.perf_counter() - t_start) > max_wall_s:
                    break  # 墙钟上限：防默认推理无休止（病理长文题）
                et = event.type
                if et == "response.output_text.delta":
                    text_parts.append(event.delta)
                elif et == "response.completed":
                    final = event.response
            return SimpleNamespace(output_text="".join(text_parts),
                                   usage=getattr(final, "usage", None),
                                   model=getattr(final, "model", model))
        kwargs = {"model": model, "messages": messages}
        for k, v in params.items():
            if v is not None:
                kwargs[k] = v
        return client.chat.completions.create(**kwargs)

    def _estimate_cost(self, model, tin, tout):
        p = self.pricing.get(model, {"in": 0, "out": 0})
        return (tin * p.get("in", 0) + tout * p.get("out", 0)) / 1_000_000

    def call(self, role, messages, max_wall_s=None, **params):
        spec = self._specs[role]
        if spec.get("dev_phase_locked") and self.phase == "dev":
            raise HoldoutLockedError(f"留出模型 {role} 开发阶段被锁定，仅阶段 7 可调用")
        if self.cap is not None and self.spent >= self.cap:
            raise BudgetExceededError(f"累计花费 {self.spent:.4f} 已达上限 {self.cap}")
        model = spec["model"]
        protocol = spec.get("api_protocol", "chat")
        client = self._get_client(role)
        for attempt in range(5):
            try:
                t0 = time.perf_counter()
                resp = self._invoke(client, model, messages, params, protocol=protocol,
                                    max_wall_s=max_wall_s)
                latency_ms = (time.perf_counter() - t0) * 1000
                break
            except TRANSIENT:
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)  # 1,2,4,8,16s 退避
        usage = getattr(resp, "usage", None)
        if protocol == "responses":
            text = resp.output_text
            tin = getattr(usage, "input_tokens", 0) or 0
            tout = getattr(usage, "output_tokens", 0) or 0
        else:
            text = resp.choices[0].message.content
            tin = getattr(usage, "prompt_tokens", 0) or 0
            tout = getattr(usage, "completion_tokens", 0) or 0
        cost = self._estimate_cost(model, tin, tout)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "model": model,
            "model_version": getattr(resp, "model", model),
            "params": params,
            "tokens_in": tin,
            "tokens_out": tout,
            "latency_ms": round(latency_ms, 2),
            "cost_cny_est": round(cost, 6),
            "api_protocol": protocol,
            "phase": self.phase,
        }
        os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self.spent += cost
        self._save_spent()
        return {"text": text, "meta": entry}

    def _save_spent(self):
        os.makedirs(os.path.dirname(self.budget_path) or ".", exist_ok=True)
        with open(self.budget_path, "w", encoding="utf-8") as f:
            json.dump({"spent_cny": self.spent}, f)
