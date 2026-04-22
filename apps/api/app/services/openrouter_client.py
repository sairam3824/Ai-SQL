from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings


class OpenRouterClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate_text(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.1,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.settings.openrouter_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenRouter is not configured. Set OPENROUTER_API_KEY to enable SQL generation.",
            )

        payload: dict[str, Any] = {
            "model": model or self.settings.openrouter_model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "HTTP-Referer": self.settings.openrouter_site_url,
            "X-Title": self.settings.openrouter_site_name,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(base_url=self.settings.openrouter_base_url, timeout=45.0) as client:
            try:
                response = await client.post("/chat/completions", json=payload, headers=headers)
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"OpenRouter request failed: {exc}",
                ) from exc

        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="OpenRouter rate limited the request. Please retry in a moment.",
            )

        if response.status_code >= 400:
            try:
                payload = response.json()
                message = payload.get("error", {}).get("message") or payload
            except Exception:
                message = response.text
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OpenRouter upstream error: {message}",
            )

        data = response.json()
        choice = data["choices"][0]["message"]
        return {
            "content": choice.get("content", ""),
            "raw": data,
        }
