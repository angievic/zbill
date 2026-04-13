from __future__ import annotations

import re
from pathlib import Path

from zbills.metrics import category_for_metric, fields_dict_for, suggestion_code
from zbills.models import Finding, Suggestion
from zbills.rules import (
    detect_cost_snippet,
    merge_suggestion_objects,
    merge_suggestions,
    score_errors,
    score_time_saved,
    score_value,
)

# Por lenguaje: regex para detectar inicio de función y nombre
PATTERNS: dict[str, list[tuple[str, re.Pattern[str]]]] = {
    "go": [
        ("func", re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?(\w+)\s*\(")),
    ],
    "javascript": [
        ("function", re.compile(r"^\s*function\s+(\w+)\s*\(")),
        ("async function", re.compile(r"^\s*async\s+function\s+(\w+)\s*\(")),
        (
            "method",
            re.compile(
                r"^\s*(?:async\s+)?(?:get|set)\s+(\w+)\s*\("
            ),
        ),
    ],
    "typescript": [
        ("function", re.compile(r"^\s*function\s+(\w+)\s*\(")),
        ("async function", re.compile(r"^\s*async\s+function\s+(\w+)\s*\(")),
    ],
    "java": [
        (
            "method",
            re.compile(
                r"^\s*(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?"
                r"(?:[\w<>\[\],\s]+\s+)+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s,.]+)?\s*\{?\s*$"
            ),
        ),
    ],
    "ruby": [
        ("def", re.compile(r"^\s*def\s+(?:self\.)?(\w+)")),
    ],
}

JS_ARROW = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:function\s*)?\([^)]*\)\s*=>"
)


def _agent_hint(name: str) -> str:
    return f"{name.lower()}_agent" if name else "your_agent"


def _window_lines(lines: list[str], start: int, max_lines: int = 120) -> tuple[str, int]:
    end = min(len(lines), start + max_lines)
    chunk = "\n".join(lines[start:end])
    return chunk, end - start


def analyze_heuristic_file(path: Path, root: Path, language: str) -> list[Finding]:
    rel = str(path.relative_to(root))
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    lines = text.splitlines()
    findings: list[Finding] = []
    patterns = list(PATTERNS.get(language, []))
    if language in ("javascript", "typescript"):
        patterns = patterns + [("arrow", JS_ARROW)]

    i = 0
    seen_at_line: set[int] = set()
    while i < len(lines):
        line = lines[i]
        name: str | None = None
        for k, rx in patterns:
            m = rx.match(line)
            if m:
                name = m.group(1)
                break
        if name is None:
            i += 1
            continue
        if i in seen_at_line:
            i += 1
            continue
        seen_at_line.add(i)

        snippet, win_len = _window_lines(lines, i)
        line_count = win_len
        agent = _agent_hint(name)
        cands: list[tuple[str, str, str, float]] = []

        v = score_value(name, snippet)
        if v >= 2.0:
            cands.append(
                (
                    "value_generated",
                    "Patrones de negocio en nombre o fragmento cercano.",
                    suggestion_code("value_generated", agent),
                    v,
                )
            )

        se = score_errors(snippet)
        if se > 0:
            cands.append(
                (
                    "errors_reduced",
                    "try/catch, validación o manejo de errores detectado en el bloque.",
                    suggestion_code("errors_reduced", agent),
                    se,
                )
            )

        st = score_time_saved(name, snippet, line_count)
        if st >= 2.5:
            cands.append(
                (
                    "time_saved",
                    "Bloque amplio o indicios de batch/API: candidato a time_saved.",
                    suggestion_code("time_saved", agent),
                    st,
                )
            )

        merged_tuples = merge_suggestions(cands)
        collected: list[Suggestion] = []
        for m, r, sug, sc in merged_tuples:
            collected.append(
                Suggestion(
                    metric=m,
                    category=category_for_metric(m),
                    reason=r,
                    suggestion=sug,
                    score=sc,
                    fields=fields_dict_for(m),
                )
            )
        collected.extend(detect_cost_snippet(snippet, agent))
        merged = merge_suggestion_objects(collected)
        if merged:
            findings.append(
                Finding(
                    file=rel,
                    function=name,
                    line=i + 1,
                    language=language,
                    suggestions=merged,
                )
            )
        i += 1

    return findings
