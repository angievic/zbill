from __future__ import annotations

import json
from pathlib import Path

from zbills.metrics import COST_METRICS, IMPACT_METRICS
from zbills.models import AnalysisReport


def write_json(report: AnalysisReport, path: Path) -> None:
    path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_markdown(report: AnalysisReport, path: Path) -> None:
    lines: list[str] = [
        "# Zbills Suggestions",
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
            f"Hallazgos (funciones): **{len(report.findings)}**",
            "",
            "---",
            "",
            "## Impact Metrics (ROI numerator)",
            "",
        ]
    )

    impact_n = 0
    for f in report.sorted_findings():
        for s in f.suggestions:
            if s.metric not in IMPACT_METRICS:
                continue
            impact_n += 1
            lines.append(
                f"### {impact_n}. `{s.metric}` — `{f.file}:{f.line}` → `{f.function}()`"
            )
            lines.append("")
            lines.append(f"> {s.reason}")
            lines.append("")
            lines.append("```python")
            lines.append(s.suggestion)
            lines.append("```")
            lines.append("")

    if impact_n == 0:
        lines.append("_No hay sugerencias de impacto en este análisis._")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Cost Metrics (ROI denominator)",
            "",
        ]
    )

    cost_n = 0
    for f in report.sorted_findings():
        for s in f.suggestions:
            if s.metric not in COST_METRICS:
                continue
            cost_n += 1
            lines.append(
                f"### {cost_n}. `{s.metric}` — `{f.file}:{f.line}` → `{f.function}()`"
            )
            lines.append("")
            lines.append(f"> {s.reason}")
            lines.append("")
            lines.append("```python")
            lines.append(s.suggestion)
            lines.append("```")
            lines.append("")

    if cost_n == 0:
        lines.append("_No hay sugerencias de costo en este análisis._")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## ROI preview (referencia)",
            "",
            "Con eventos enviados a Zpulse (`POST .../api/v1/events`) y resumen `GET .../api/v1/summary?days=30`:",
            "",
            "```text",
            "ROI % ≈ (total_impact_usd - total_cost_usd) / total_cost_usd × 100  (según agregación del backend)",
            "```",
            "",
            "`cost_llm.value` debe alinearse con `cost_input + cost_output` (tolerancia típica 0.01).",
            "",
        ]
    )

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
            lines.append(
                f"{i}. {f.file}::{f.function}  →  {top.metric} [{top.category}] ({reason_display})"
            )
        else:
            lines.append(f"{i}. {f.file}::{f.function}")
        lines.append("")
    return "\n".join(lines)
