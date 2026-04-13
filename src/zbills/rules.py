"""Métricas ROI y reglas de puntuación (v2: impacto + costo)."""

from __future__ import annotations

import re
from typing import Iterable

from zbills.metrics import category_for_metric, fields_dict_for, suggestion_code
from zbills.models import Suggestion

# Nombres / palabras que apuntan a valor de negocio
VALUE_KEYWORDS = re.compile(
    r"(create_|process_|handle_|resolve_|charge|payment|invoice|"
    r"lead|order|sale|subscribe|checkout|ticket|user|account|billing|refund)",
    re.I,
)

BATCH_KEYWORDS = re.compile(
    r"\b(batch|bulk|queue|worker|cron|schedule|sync|import|export)\b",
    re.I,
)

ERROR_KEYWORDS = re.compile(
    r"\b(try\s*\{|except|catch\s*\(|finally|retry|validate|raise\s+|"
    r"Error\(|logger\.(error|exception)|log\.error)\b",
    re.I,
)

API_KEYWORDS = re.compile(
    r"\b(requests\.|httpx\.|fetch\s*\(|axios\.|http\.(Get|Post)|"
    r"urllib|RestTemplate|http\.Client)\b",
    re.I,
)

LOOP_KEYWORDS = re.compile(r"\b(for\s*\(|while\s*\(|for\s+\w+\s+in\s+)\b", re.I)

# --- Detección de costos (heurística por texto) ---
LLM_SDK = re.compile(
    r"(openai\.|anthropic\.|litellm|langchain|ChatOpenAI|ChatAnthropic|"
    r"GenerativeModel|genai\.|google\.generativeai|ollama\.|"
    r"chat\.completions\.create|messages\.create|completions\.create)",
    re.I,
)
COMPUTE_CLOUD = re.compile(
    r"(boto3\.(client|resource)\s*\(\s*['\"](ec2|ecs|lambda|batch)|"
    r"google\.cloud\.compute|kubernetes|subprocess\.(run|Popen)|"
    r"azure\.mgmt\.compute|docker\.|\.Client\s*\(\s*['\"]compute)",
    re.I,
)
STORAGE = re.compile(
    r"(boto3\.(client|resource)\s*\(\s*['\"]s3|google\.cloud\.storage|azure\.storage|"
    r"BlobClient|upload_file|bulk_insert|INSERT\s+INTO\s+\w+\s+SELECT)",
    re.I,
)
API_HTTP = re.compile(
    r"(requests\.(get|post|put|patch|delete)|httpx\.|aiohttp\.|urllib\.|"
    r"fetch\s*\(|axios\.|RestTemplate|stripe\.|twilio\.|sendgrid)",
    re.I,
)
HUMAN_LOOP = re.compile(
    r"(assign_to|send_for_review|approval|human[_\s]?in[_\s]?the[_\s]?loop|"
    r"wait_for_human|slack\.|mail\.|smtp\.|notify.*review)",
    re.I,
)
OTHER_PAID = re.compile(
    r"(datadog|sentry|newrelic|segment\.|mixpanel|webhook.*post)",
    re.I,
)


def example_track(metric: str, agent_hint: str = "your_agent") -> str:
    """Compat: devuelve zbills.track corto."""
    return suggestion_code(metric, agent_hint)


def example_decorator(metric: str, agent_hint: str = "your_agent") -> str:
    return f"@track_{metric}(agent=\"{agent_hint}\")\ndef ..."


def score_value(name: str, snippet: str) -> float:
    s = 0.0
    if VALUE_KEYWORDS.search(name):
        s += 4.0
    if VALUE_KEYWORDS.search(snippet):
        s += 2.0
    return min(s, 10.0)


def score_errors(snippet: str) -> float:
    if ERROR_KEYWORDS.search(snippet):
        return min(3.0 + snippet.lower().count("except") * 0.5, 9.0)
    return 0.0


def score_time_saved(name: str, snippet: str, line_count: int, threshold_long: int = 35) -> float:
    s = 0.0
    if line_count >= threshold_long:
        s += 3.0 + min((line_count - threshold_long) / 20.0, 3.0)
    if BATCH_KEYWORDS.search(name) or BATCH_KEYWORDS.search(snippet):
        s += 2.5
    if LOOP_KEYWORDS.search(snippet) and line_count >= 15:
        s += 1.5
    if API_KEYWORDS.search(snippet) and line_count >= 10:
        s += 1.0
    return min(s, 10.0)


def merge_suggestions(
    candidates: Iterable[tuple[str, str, str, float]],
) -> list[tuple[str, str, str, float]]:
    """Deduplica por métrica, conserva mayor score (legacy tuple)."""
    best: dict[str, tuple[str, str, str, float]] = {}
    for metric, reason, example, score in candidates:
        prev = best.get(metric)
        if prev is None or score > prev[3]:
            best[metric] = (metric, reason, example, score)
    return sorted(best.values(), key=lambda x: x[3], reverse=True)


def detect_cost_snippet(snippet: str, agent: str) -> list[Suggestion]:
    """Heurísticas de métricas de costo sobre texto de función/bloque."""
    out: list[Suggestion] = []
    s = snippet

    if LLM_SDK.search(s):
        out.append(
            Suggestion(
                metric="cost_llm",
                category=category_for_metric("cost_llm"),
                reason="LLM call detected — track tokens and cost per call",
                suggestion=suggestion_code("cost_llm", agent),
                score=7.5,
                fields=fields_dict_for("cost_llm"),
            )
        )

    if COMPUTE_CLOUD.search(s):
        out.append(
            Suggestion(
                metric="cost_compute",
                category=category_for_metric("cost_compute"),
                reason="Cloud/compute or subprocess workload — track infra cost",
                suggestion=suggestion_code("cost_compute", agent),
                score=6.8,
                fields=fields_dict_for("cost_compute"),
            )
        )

    if STORAGE.search(s):
        out.append(
            Suggestion(
                metric="cost_storage",
                category=category_for_metric("cost_storage"),
                reason="Storage operation detected — track data cost",
                suggestion=suggestion_code("cost_storage", agent),
                score=6.5,
                fields=fields_dict_for("cost_storage"),
            )
        )

    if HUMAN_LOOP.search(s):
        out.append(
            Suggestion(
                metric="cost_human",
                category=category_for_metric("cost_human"),
                reason="Human-in-the-loop detected — track review/approval hours",
                suggestion=suggestion_code("cost_human", agent),
                score=6.2,
                fields=fields_dict_for("cost_human"),
            )
        )

    if OTHER_PAID.search(s) and not LLM_SDK.search(s):
        out.append(
            Suggestion(
                metric="cost_other",
                category=category_for_metric("cost_other"),
                reason="Paid service integration detected — track misc cost",
                suggestion=suggestion_code("cost_other", agent),
                score=5.5,
                fields=fields_dict_for("cost_other"),
            )
        )

    # API externa no-LLM: HTTP/SDK pero no patrón LLM previo
    if API_HTTP.search(s) and not LLM_SDK.search(s):
        out.append(
            Suggestion(
                metric="cost_api",
                category=category_for_metric("cost_api"),
                reason="External API call detected — track per-call cost",
                suggestion=suggestion_code("cost_api", agent),
                score=6.0,
                fields=fields_dict_for("cost_api"),
            )
        )

    return out


def merge_suggestion_objects(suggestions: list[Suggestion]) -> list[Suggestion]:
    best: dict[str, Suggestion] = {}
    for s in suggestions:
        prev = best.get(s.metric)
        if prev is None or s.score > prev.score:
            best[s.metric] = s
    return sorted(best.values(), key=lambda x: x.score, reverse=True)
