from __future__ import annotations

import re
from pathlib import Path

from zbills.models import Finding, Suggestion
from zbills.rules import (
    example_track,
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
            ),  # class getters sometimes
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

# JS/TS: const foo = async () => or function expr
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
        kind = ""
        for k, rx in patterns:
            m = rx.match(line)
            if m:
                name = m.group(1)
                kind = k
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
                    example_track("value_generated", agent),
                    v,
                )
            )

        se = score_errors(snippet)
        if se > 0:
            cands.append(
                (
                    "errors_reduced",
                    "try/catch, validación o manejo de errores detectado en el bloque.",
                    example_track("errors_reduced", agent),
                    se,
                )
            )

        st = score_time_saved(name, snippet, line_count)
        if st >= 2.5:
            cands.append(
                (
                    "time_saved",
                    "Bloque amplio o indicios de batch/API: candidato a time_saved.",
                    example_track("time_saved", agent),
                    st,
                )
            )

        merged = merge_suggestions(cands)
        if merged:
            suggestions = [
                Suggestion(metric=m, reason=r, example=e, score=sc) for m, r, e, sc in merged
            ]
            findings.append(
                Finding(
                    file=rel,
                    function=name,
                    line=i + 1,
                    language=language,
                    suggestions=suggestions,
                )
            )
        i += 1

    return findings
