from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from zbills.llm.config import LLMConfig


class LLMError(RuntimeError):
    pass


def _http_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
    method: str = "POST",
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    prev = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        raise LLMError(f"HTTP {e.code} {e.reason}: {err_body[:800]}") from e
    except urllib.error.URLError as e:
        raise LLMError(f"Red: {e.reason}") from e
    finally:
        socket.setdefaulttimeout(prev)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise LLMError(f"Respuesta no JSON: {raw[:400]}") from e


def chat_completion(
    cfg: LLMConfig,
    system: str,
    user: str,
) -> str:
    if cfg.provider == "openai":
        return _openai(cfg, system, user)
    if cfg.provider == "anthropic":
        return _anthropic(cfg, system, user)
    if cfg.provider == "gemini":
        return _gemini(cfg, system, user)
    if cfg.provider == "ollama":
        return _ollama(cfg, system, user)
    raise LLMError(f"Proveedor no soportado: {cfg.provider}")


def _openai(cfg: LLMConfig, system: str, user: str) -> str:
    if not cfg.openai_api_key:
        raise LLMError("Falta OPENAI_API_KEY (o ZBILLS_OPENAI_API_KEY)")
    data = _http_json(
        "https://api.openai.com/v1/chat/completions",
        {
            "model": cfg.model,
            "temperature": cfg.temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        {
            "Authorization": f"Bearer {cfg.openai_api_key}",
            "Content-Type": "application/json",
        },
        cfg.timeout_sec,
    )
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise LLMError(f"Formato OpenAI inesperado: {data!r}") from e


def _anthropic(cfg: LLMConfig, system: str, user: str) -> str:
    if not cfg.anthropic_api_key:
        raise LLMError("Falta ANTHROPIC_API_KEY (o ZBILLS_ANTHROPIC_API_KEY)")
    data = _http_json(
        "https://api.anthropic.com/v1/messages",
        {
            "model": cfg.model,
            "max_tokens": 4096,
            "temperature": cfg.temperature,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
        {
            "x-api-key": cfg.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        cfg.timeout_sec,
    )
    try:
        parts = data["content"]
        if isinstance(parts, list) and parts:
            return str(parts[0].get("text", ""))
        return str(data)
    except (KeyError, TypeError) as e:
        raise LLMError(f"Formato Anthropic inesperado: {data!r}") from e


def _gemini(cfg: LLMConfig, system: str, user: str) -> str:
    if not cfg.gemini_api_key:
        raise LLMError("Falta GOOGLE_API_KEY / GEMINI_API_KEY / ZBILLS_GEMINI_API_KEY")
    model = cfg.model
    if not model.startswith("models/"):
        model_path = f"models/{model}"
    else:
        model_path = model
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"{model_path}:generateContent?key={urllib.parse.quote(cfg.gemini_api_key)}"
    )

    full_user = f"{system}\n\n---\n\n{user}"
    data = _http_json(
        url,
        {
            "contents": [{"parts": [{"text": full_user}]}],
            "generationConfig": {
                "temperature": cfg.temperature,
            },
        },
        {"Content-Type": "application/json"},
        cfg.timeout_sec,
    )
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    except (KeyError, IndexError, TypeError) as e:
        raise LLMError(f"Formato Gemini inesperado: {data!r}") from e


def _ollama(cfg: LLMConfig, system: str, user: str) -> str:
    base = cfg.ollama_base_url.rstrip("/")
    data = _http_json(
        f"{base}/api/chat",
        {
            "model": cfg.model,
            "stream": False,
            "options": {"temperature": cfg.temperature},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        {"Content-Type": "application/json"},
        cfg.timeout_sec,
    )
    try:
        return str(data["message"]["content"])
    except (KeyError, TypeError) as e:
        raise LLMError(f"Formato Ollama inesperado: {data!r}") from e
