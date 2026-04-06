"""Métricas ROI y reglas de puntuación (V1 heurística)."""

from __future__ import annotations

import re
from typing import Iterable

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


def example_track(metric: str, agent_hint: str = "your_agent") -> str:
    return (
        f"track(agent='{agent_hint}', metric='{metric}', value=...)"
    )


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
    """Deduplica por métrica, conserva mayor score."""
    best: dict[str, tuple[str, str, str, float]] = {}
    for metric, reason, example, score in candidates:
        prev = best.get(metric)
        if prev is None or score > prev[3]:
            best[metric] = (metric, reason, example, score)
    return sorted(best.values(), key=lambda x: x[3], reverse=True)
