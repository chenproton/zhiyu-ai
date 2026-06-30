import json
import httpx
from typing import AsyncIterator, List, Dict, Any, Optional
from config import settings


async def complete_deepseek(
    system_prompt: str,
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    if not settings.DEEPSEEK_API_KEY:
        return '{"name":"AI 助手","description":"一个通用的 AI 对话助手。","prompt":"你是一位 helpful 的 AI 助手。","welcome_msg":"你好！有什么可以帮您的？"}'

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for h in history:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": question})

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "stream": False,
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def stream_deepseek(
    system_prompt: str,
    question: str,
    history: Optional[List[Dict[str, str]]] = None
) -> AsyncIterator[str]:
    if not settings.DEEPSEEK_API_KEY:
        # 未配置 API 时返回演示答案
        yield "当前未配置 DeepSeek API Key，这是演示回复。"
        yield "如需真实 AI 回复，请在 .env 中配置 DEEPSEEK_API_KEY。"
        return

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for h in history:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": question})

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream(
            "POST",
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "stream": True,
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield content
                    except Exception:
                        continue
