from functools import lru_cache

from app.core.config import get_settings


@lru_cache
def load_prompt(name: str) -> str:
    settings = get_settings()
    path = settings.prompt_dir / name
    return path.read_text(encoding="utf-8")
