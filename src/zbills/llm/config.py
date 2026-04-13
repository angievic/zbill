from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

Provider = Literal["ollama", "openai", "anthropic", "gemini"]

# Por defecto: Ollama + Mistral (local, buen balance código / razonamiento)
DEFAULT_PROVIDER: Provider = "ollama"
DEFAULT_MODEL_BY_PROVIDER: dict[str, str] = {
    "ollama": "mistral",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-20241022",
    "gemini": "gemini-3.1-flash-lite-preview",
}


@dataclass
class LLMConfig:
    provider: Provider
    model: str
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    ollama_base_url: str = "http://127.0.0.1:11434"
    timeout_sec: float = 120.0
    temperature: float = 0.2


def _pick_str(*names: str, default: str = "") -> str:
    for n in names:
        v = os.environ.get(n)
        if v is not None and str(v).strip():
            return str(v).strip()
    return default


def load_llm_config(
    provider: str | None = None,
    model: str | None = None,
) -> LLMConfig:
    p_raw = (provider or _pick_str("ZBILLS_LLM_PROVIDER", default=DEFAULT_PROVIDER)).lower()
    if p_raw not in ("ollama", "openai", "anthropic", "gemini"):
        raise ValueError(
            f"ZBILLS_LLM_PROVIDER inválido: {p_raw!r}. "
            "Usa: ollama, openai, anthropic, gemini"
        )
    prov: Provider = p_raw  # type: ignore[assignment]

    default_model = DEFAULT_MODEL_BY_PROVIDER[prov]
    # CLI `--model` gana sobre ZBILLS_LLM_MODEL si ambos existen
    m = (model or _pick_str("ZBILLS_LLM_MODEL", default="") or default_model)

    return LLMConfig(
        provider=prov,
        model=m,
        openai_api_key=_pick_str("OPENAI_API_KEY", "ZBILLS_OPENAI_API_KEY") or None,
        anthropic_api_key=_pick_str("ANTHROPIC_API_KEY", "ZBILLS_ANTHROPIC_API_KEY") or None,
        gemini_api_key=_pick_str(
            "GOOGLE_API_KEY",
            "GEMINI_API_KEY",
            "ZBILLS_GEMINI_API_KEY",
        )
        or None,
        ollama_base_url=_pick_str("OLLAMA_HOST", "ZBILLS_OLLAMA_URL", default="http://127.0.0.1:11434"),
        timeout_sec=float(_pick_str("ZBILLS_LLM_TIMEOUT", default="120") or "120"),
        temperature=float(_pick_str("ZBILLS_LLM_TEMPERATURE", default="0.2") or "0.2"),
    )
