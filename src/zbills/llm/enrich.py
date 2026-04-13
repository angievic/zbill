from __future__ import annotations

import json
import re
from pathlib import Path

from zbills.llm.config import LLMConfig
from zbills.llm.providers import LLMError, chat_completion
from zbills.metrics import ALL_METRICS, category_for_metric, fields_dict_for, suggestion_code
from zbills.models import Finding, Suggestion

SYSTEM_PROMPT = """Eres ZBILLS Analyzer (Zpulse v2). Hay 9 métricas válidas:

IMPACTO (numerador ROI): time_saved, errors_reduced, value_generated
COSTO (denominador ROI): cost_llm, cost_compute, cost_api, cost_storage, cost_human, cost_other

- cost_llm: llamadas a LLM — requiere provider, model, tokens_input/output, cost_input/output; value ≈ cost_input+cost_output
- cost_compute: cloud/GPU/subprocess/Kubernetes
- cost_api: APIs HTTP/SDK externos (no LLM)
- cost_storage: S3, GCS, DB masivo, uploads
- cost_human: approval, revisión humana, colas
- cost_other: observabilidad de pago, webhooks a servicios de pago, etc.

Prioriza hallazgos donde en el mismo flujo haya impacto (time_saved/value_generated) Y costo (p. ej. cost_llm) para ROI completo.

Responde SOLO JSON (sin markdown), forma:
{
  "agent_hint": "snake_case",
  "rationale": "una frase",
  "suggestions": [
    {
      "metric": "una de las 9",
      "category": "impact|cost",
      "reason": "breve",
      "suggestion": "zbills.track(...)",
      "fields": { "required": [...], "optional": [...] }
    }
  ]
}
Máximo 6 sugerencias. Usa zbills.track en suggestion."""


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
        if m not in ALL_METRICS:
            continue
        cat = str(item.get("category", "")).strip() or category_for_metric(m)
        reason = str(item.get("reason", "")).strip() or "Sugerencia LLM"
        sug = str(item.get("suggestion", item.get("example", ""))).strip()
        if not sug:
            sug = suggestion_code(m, agent)
        score = 6.0
        fd = item.get("fields")
        fields = None
        if isinstance(fd, dict) and ("required" in fd or "optional" in fd):
            fields = {
                "required": list(fd.get("required", [])),
                "optional": list(fd.get("optional", [])),
            }
        else:
            fields = fields_dict_for(m)
        out.append(
            Suggestion(
                metric=m,
                category=cat,
                reason=reason,
                suggestion=sug,
                score=score,
                fields=fields,
            )
        )
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
            "Refina o reemplaza sugerencias según el código real. "
            "Si hay llamada LLM, prioriza cost_llm con tokens; si hay impacto y costo en el mismo flujo, inclúyelos."
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
