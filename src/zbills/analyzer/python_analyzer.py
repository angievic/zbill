from __future__ import annotations

import ast
from pathlib import Path

from zbills.models import Finding, Suggestion
from zbills.rules import (
    example_track,
    merge_suggestions,
    score_errors,
    score_time_saved,
    score_value,
)


def _body_lines(node: ast.AST) -> int:
    if hasattr(node, "end_lineno") and hasattr(node, "lineno"):
        lo = getattr(node, "lineno", 1)
        hi = getattr(node, "end_lineno", lo)
        return max(1, hi - lo + 1)
    return 1


def _snippet_from_body(source: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    lines = source.splitlines()
    if hasattr(node, "end_lineno") and hasattr(node, "lineno"):
        lo = node.lineno - 1
        hi = node.end_lineno
        return "\n".join(lines[lo:hi])
    return source


def _has_try(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Try):
            return True
    if hasattr(ast, "TryStar"):
        for child in ast.walk(node):
            if isinstance(child, ast.TryStar):
                return True
    return False


def _has_loops(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.For | ast.While | ast.AsyncFor):
            return True
    return False


def _agent_hint_from_name(name: str) -> str:
    base = name.strip("_").lower() or "agent"
    return f"{base}_agent"


def analyze_python_file(path: Path, root: Path) -> list[Finding]:
    rel = str(path.relative_to(root))
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    findings: list[Finding] = []

    class V(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._process(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._process(node)

        def _process(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            if node.name.startswith("_") and not node.name.startswith("__"):
                return
            name = node.name
            body_lines = _body_lines(node)
            snippet = _snippet_from_body(source, node)
            agent = _agent_hint_from_name(name)
            cands: list[tuple[str, str, str, float]] = []

            v = score_value(name, snippet)
            if v >= 2.0:
                cands.append(
                    (
                        "value_generated",
                        "Nombre o cuerpo alineado con flujos de negocio (creación, cobro, lead, etc.).",
                        example_track("value_generated", agent),
                        v,
                    )
                )

            if _has_try(node):
                se = score_errors(snippet)
                cands.append(
                    (
                        "errors_reduced",
                        "Bloque try/except: buen lugar para medir fallos evitados o recuperación.",
                        example_track("errors_reduced", agent),
                        max(se, 4.0),
                    )
                )

            st = score_time_saved(name, snippet, body_lines)
            if _has_loops(node) and body_lines >= 12:
                st = max(st, 4.0)
            if st >= 2.5:
                cands.append(
                    (
                        "time_saved",
                        "Función larga, loops o I/O: candidata a ahorro de tiempo / automatización.",
                        example_track("time_saved", agent),
                        st,
                    )
                )

            merged = merge_suggestions(cands)
            if not merged:
                return
            suggestions = [
                Suggestion(metric=m, reason=r, example=e, score=sc) for m, r, e, sc in merged
            ]
            findings.append(
                Finding(
                    file=rel,
                    function=name,
                    line=node.lineno,
                    language="python",
                    suggestions=suggestions,
                )
            )

    V().visit(tree)
    return findings
