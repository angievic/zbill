from __future__ import annotations

import json
import re
from pathlib import Path

from zbills.llm.config import LLMConfig
from zbills.llm.providers import LLMError, chat_completion
from zbills.models import Finding, Suggestion

SYSTEM_PROMPT = """Eres ZBILLS Analyzer. Sugieres instrumentación ROI en código.
Métricas típicas: time_saved, errors_reduced, value_generated.
Responde SOLO con un objeto JSON válido (sin markdown), con esta forma exacta:
{
  "agent_hint": "snake_case sugerido para el agente",
  "rationale": "una frase breve",
  "suggestions": [
    {
      "metric": "time_saved|errors_reduced|value_generated",
      "reason": "por qué aquí",
      "example": "track(agent='...', metric='...', value=...)"
    }
  ]
}
Máximo 4 sugerencias. Prioriza las más accionables."""


def _extract_json_block(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.I)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)


def _read_snippet(root: Path, rel_file: str, line: int, before: int = 2, after: int = 45) -> str:
    path = (root / rel_file).resolve()
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    lo = max(0, line - 1 - before)
    hi = min(len(lines), line - 1 + after)
    return "\n".join(f"{i + 1:4d} | {lines[i]}" for i in range(lo, hi))


def _parse_llm_response(raw: str) -> tuple[str, str, list[Suggestion]]:
    data = _extract_json_block(raw)
    agent = str(data.get("agent_hint", "your_agent")).strip() or "your_agent"
    rationale = str(data.get("rationale", "")).strip()
    out: list[Suggestion] = []
    for item in data.get("suggestions") or []:
        if not isinstance(item, dict):
            continue
        m = str(item.get("metric", "")).strip()
        if m not in ("time_saved", "errors_reduced", "value_generated"):
            continue
        reason = str(item.get("reason", "")).strip() or "Sugerencia LLM"
        example = str(item.get("example", "")).strip() or f"track(agent='{agent}', metric='{m}', value=...)"
        out.append(Suggestion(metric=m, reason=reason, example=example, score=6.0))
    return agent, rationale, out


def enrich_findings(
    root: Path,
    findings: list[Finding],
    cfg: LLMConfig,
    top_n: int,
) -> None:
    """En sitio: añade metadatos LLM y sustituye sugerencias si el modelo respondió bien."""
    root = root.resolve()
    for f in findings[:top_n]:
        snippet = _read_snippet(root, f.file, f.line)
        static_summary = json.dumps(
            [s.to_dict() for s in f.suggestions],
            ensure_ascii=False,
        )
        user = (
            f"Archivo: {f.file}\n"
            f"Función: {f.function}\n"
            f"Línea aproximada: {f.line}\n"
            f"Lenguaje: {f.language}\n\n"
            f"Sugerencias estáticas (JSON): {static_summary}\n\n"
            f"Fragmento de código:\n```\n{snippet}\n```\n\n"
            "Refina o reemplaza sugerencias según el código real."
        )
        try:
            raw = chat_completion(cfg, SYSTEM_PROMPT, user)
            agent, rationale, llm_sugs = _parse_llm_response(raw)
        except (LLMError, json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            f.llm = {
                "ok": False,
                "error": str(e),
                "provider": cfg.provider,
                "model": cfg.model,
            }
            continue

        if llm_sugs:
            f.suggestions = llm_sugs
        f.llm = {
            "ok": True,
            "provider": cfg.provider,
            "model": cfg.model,
            "agent_hint": agent,
            "rationale": rationale,
            "used_static_suggestions": not bool(llm_sugs),
        }
