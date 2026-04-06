from __future__ import annotations

import json
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any

from zbills.llm.config import LLMConfig


class LLMSetupError(RuntimeError):
    """Fallo de configuración antes de llamar al LLM (credenciales, Ollama, modelo)."""


def _http_get_json(url: str, timeout: float) -> dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    prev = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    finally:
        socket.setdefaulttimeout(prev)
    return json.loads(raw)


def _ollama_tag_names(base_url: str, timeout: float) -> list[str]:
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        data = _http_get_json(url, timeout=min(timeout, 30.0))
    except urllib.error.URLError as e:
        win = (
            "\nSi no tienes Ollama instalado (Windows): https://ollama.com/download/windows\n"
            if _is_windows()
            else ""
        )
        raise LLMSetupError(
            "No se pudo conectar con Ollama en "
            f"{base_url!r}: {e.reason}\n\n"
            "Arranca la aplicación Ollama (icono en la barra) o revisa OLLAMA_HOST."
            + win
        ) from e
    except (TimeoutError, OSError, json.JSONDecodeError) as e:
        raise LLMSetupError(f"No se pudo leer /api/tags de Ollama: {e}") from e
    models = data.get("models") or []
    return [str(m.get("name", "")) for m in models if isinstance(m, dict)]


def _model_matches_installed(wanted: str, installed: list[str]) -> bool:
    w = wanted.strip().lower()
    if not w:
        return False
    w_base = w.split(":", 1)[0]
    for tag in installed:
        t = tag.strip().lower()
        if not t:
            continue
        t_base = t.split(":", 1)[0]
        if t == w or t.startswith(w + ":") or w_base == t_base:
            return True
    return False


def _is_windows() -> bool:
    return sys.platform.startswith("win")


def _windows_ollama_instructions(model: str) -> str:
    return (
        f"El modelo Ollama {model!r} no está instalado (o no aparece en /api/tags).\n\n"
        "En Windows:\n"
        "  1. Descarga e instala Ollama: https://ollama.com/download/windows\n"
        "  2. Abre **PowerShell** o **cmd** y ejecuta:\n\n"
        f"       ollama pull {model}\n\n"
        "  3. Comprueba que la app Ollama esté en ejecución y vuelve a lanzar:\n\n"
        "       zbills analyze . --llm\n"
    )


def _ollama_download_url() -> str:
    if sys.platform == "darwin":
        return "https://ollama.com/download/mac"
    return "https://ollama.com/download/linux"


def _unix_run_ollama_pull(model: str) -> None:
    exe = shutil.which("ollama")
    if not exe:
        raise LLMSetupError(
            "El modelo no está instalado y no se encontró el comando `ollama` en el PATH.\n\n"
            f"Instala Ollama: {_ollama_download_url()}\n"
            "Luego ejecuta en una terminal:\n\n"
            f"  ollama pull {model}\n"
        )
    print(f"Descargando modelo con Ollama: ollama pull {model}", file=sys.stderr)
    r = subprocess.run(
        [exe, "pull", model],
        stdin=subprocess.DEVNULL,
    )
    if r.returncode != 0:
        raise LLMSetupError(
            f"`ollama pull {model}` falló (código {r.returncode}). "
            "Revisa la salida anterior o ejecuta el pull manualmente."
        )


def _ensure_ollama_model(cfg: LLMConfig) -> None:
    tags = _ollama_tag_names(cfg.ollama_base_url, cfg.timeout_sec)
    if _model_matches_installed(cfg.model, tags):
        return

    if _is_windows():
        raise LLMSetupError(_windows_ollama_instructions(cfg.model))

    _unix_run_ollama_pull(cfg.model)

    tags2 = _ollama_tag_names(cfg.ollama_base_url, cfg.timeout_sec)
    if not _model_matches_installed(cfg.model, tags2):
        raise LLMSetupError(
            f"Tras `ollama pull`, el modelo {cfg.model!r} sigue sin aparecer en Ollama. "
            f"Modelos visibles: {', '.join(tags2[:12])}"
            + ("…" if len(tags2) > 12 else "")
        )


def _third_party_credentials_message(provider: str) -> str:
    common = (
        "\nO usa LLM **local** sin API keys:\n"
        "  export ZBILLS_LLM_PROVIDER=ollama\n"
        "  export ZBILLS_LLM_MODEL=mistral\n"
        "  (en macOS/Linux, zbills intentará `ollama pull` si falta el modelo)\n"
    )
    if provider == "openai":
        return (
            "Falta API key de OpenAI. Define una de:\n"
            "  export OPENAI_API_KEY=sk-...\n"
            "  export ZBILLS_OPENAI_API_KEY=sk-...\n" + common
        )
    if provider == "anthropic":
        return (
            "Falta API key de Anthropic. Define una de:\n"
            "  export ANTHROPIC_API_KEY=...\n"
            "  export ZBILLS_ANTHROPIC_API_KEY=...\n" + common
        )
    if provider == "gemini":
        return (
            "Falta API key de Google (Gemini). Define una de:\n"
            "  export GOOGLE_API_KEY=...\n"
            "  export GEMINI_API_KEY=...\n"
            "  export ZBILLS_GEMINI_API_KEY=...\n" + common
        )
    return "Faltan credenciales para el proveedor LLM configurado." + common


def prepare_llm(cfg: LLMConfig) -> None:
    """
    Valida credenciales (APIs cloud) y, para Ollama, asegura que el modelo exista:
    en macOS/Linux ejecuta `ollama pull` si hace falta; en Windows muestra instrucciones.
    """
    if cfg.provider == "openai" and not cfg.openai_api_key:
        raise LLMSetupError(_third_party_credentials_message("openai"))
    if cfg.provider == "anthropic" and not cfg.anthropic_api_key:
        raise LLMSetupError(_third_party_credentials_message("anthropic"))
    if cfg.provider == "gemini" and not cfg.gemini_api_key:
        raise LLMSetupError(_third_party_credentials_message("gemini"))
    if cfg.provider == "ollama":
        _ensure_ollama_model(cfg)
