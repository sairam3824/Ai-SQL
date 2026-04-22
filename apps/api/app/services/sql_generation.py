import json
from typing import Any

from fastapi import HTTPException, status

from app.schemas.chat import SqlGenerationResponse
from app.schemas.schema import SchemaResponse
from app.services.openrouter_client import OpenRouterClient
from app.services.prompt_loader import load_prompt


class SqlGenerationService:
    def __init__(self) -> None:
        self.client = OpenRouterClient()

    async def generate(
        self,
        dialect: str,
        schema: SchemaResponse,
        question: str,
        chat_context: list[dict[str, Any]],
        session_id: str,
    ) -> SqlGenerationResponse:
        system_prompt = load_prompt("sql_generation_system.txt")
        user_template = load_prompt("sql_generation_user.txt")
        context = "\n".join(f"{item['role']}: {item['content']}" for item in chat_context[-6:]) or "No prior context."
        user_prompt = user_template.format(
            dialect=dialect,
            schema_summary=schema.summary,
            chat_context=context,
            question=question,
        )

        response = await self.client.generate_text(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = response["content"]
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Model returned invalid JSON: {content}",
            ) from exc

        return SqlGenerationResponse(
            session_id=session_id,
            sql=payload.get("sql", "").strip(),
            explanation=payload.get("explanation", "").strip(),
            assumptions=payload.get("assumptions", []),
            warnings=payload.get("warnings", []),
            visualization_suggestion=payload.get("visualization_suggestion"),
            confidence=payload.get("confidence", "medium"),
        )
