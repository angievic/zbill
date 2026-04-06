from __future__ import annotations

import json
from pathlib import Path

from zbills.models import AnalysisReport


def write_json(report: AnalysisReport, path: Path) -> None:
    path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_markdown(report: AnalysisReport, path: Path) -> None:
    lines: list[str] = [
        "# ZBILLS — sugerencias de instrumentación ROI",
        "",
    ]
    if report.runtime:
        r = report.runtime
        lines.extend(
            [
                "## Runtime",
                "",
                f"- **Run ID**: `{r.get('run_id', '')}`",
                f"- **Carpeta**: `{r.get('run_folder', '')}`",
                f"- **Inicio (UTC)**: {r.get('started_at', '')}",
                f"- **Fin (UTC)**: {r.get('finished_at', '')}",
                f"- **Duración (s)**: {r.get('duration_seconds', '')}",
                f"- **zbills**: {r.get('zbills_version', '')}",
                "",
                "---",
                "",
            ]
        )
    lines.extend(
        [
            f"Raíz analizada: `{report.root}`",
            f"Oportunidades: **{len(report.findings)}**",
            "",
        ]
    )
    for i, f in enumerate(report.sorted_findings(), start=1):
        lines.append(f"## {i}. `{f.file}` — `{f.function}` (L{f.line})")
        lines.append("")
        if f.llm and f.llm.get("ok"):
            lines.append(
                f"> **LLM** ({f.llm.get('provider')}/{f.llm.get('model')}): "
                f"{f.llm.get('rationale', '')}"
            )
            lines.append("")
        for s in f.suggestions:
            lines.append(f"- **{s.metric}** (score {s.score:.1f}): {s.reason}")
            lines.append(f"  - Ejemplo: `{s.example}`")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def format_console(report: AnalysisReport) -> str:
    lines = [
        "",
        "🔍 ZBILLS Analysis Complete",
        "",
    ]
    if report.llm and report.llm.get("enabled"):
        lines.append(
            f"LLM: {report.llm.get('provider')}/{report.llm.get('model')} "
            f"(enriched top {report.llm.get('enriched_top')})"
        )
        lines.append("")
    lines.append(f"Found {len(report.findings)} ROI opportunities:")
    lines.append("")
    for i, f in enumerate(report.sorted_findings(), start=1):
        top = f.suggestions[0] if f.suggestions else None
        if top:
            reason_display = top.reason if len(top.reason) <= 60 else top.reason[:57] + "…"
            lines.append(f"{i}. {f.file}::{f.function}  →  {top.metric} ({reason_display})")
        else:
            lines.append(f"{i}. {f.file}::{f.function}")
        lines.append("")
    return "\n".join(lines)
