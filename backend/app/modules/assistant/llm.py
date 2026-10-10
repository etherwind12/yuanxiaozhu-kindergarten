"""AI 助手 —— DeepSeek 接入（可选）。

未配置 Key 时 `enabled()` 为 False，调用方自动回退本地规则引擎；
网络异常 / 超时一律静默降级，保证离线环境同样可用。
大模型只负责「把已检索到的事实说得更自然」，不产生、不篡改数据。
"""

import httpx

from app.core.config import settings

_TIMEOUT = httpx.Timeout(6.0, connect=4.0)


def enabled() -> bool:
    return bool(settings.DEEPSEEK_API_KEY)


def _chat(messages: list[dict], temperature: float = 0.3) -> str | None:
    try:
        resp = httpx.post(
            f"{settings.DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
            json={
                "model": settings.DEEPSEEK_MODEL,
                "messages": messages,
                "temperature": temperature,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return None


def polish(question: str, facts: str) -> str | None:
    """把规则引擎检索出的事实润色为自然口语回答。"""
    system = (
        "你是幼儿园园务资产管理系统里的助手『园小助』。"
        "请依据给定的查询结果，用简洁、专业、友好的中文回答用户，1~3 句即可。"
        "只依据给定数据作答，不得编造数字，不要输出 Markdown 表格。"
    )
    user = f"用户问题：{question}\n\n查询结果（事实，不可篡改）：\n{facts}"
    out = _chat([{"role": "system", "content": system}, {"role": "user", "content": user}])
    return out.strip() if out else None
