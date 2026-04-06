from __future__ import annotations

from pathlib import Path

from zbills.analyzer.heuristic_analyzer import analyze_heuristic_file
from zbills.analyzer.python_analyzer import analyze_python_file
from zbills.discovery import iter_source_files
from zbills.models import AnalysisReport, Finding


def analyze_project(root: str | Path, max_findings: int | None = None) -> AnalysisReport:
    r = Path(root).resolve()
    findings: list[Finding] = []

    for path, lang in iter_source_files(r):
        if lang == "python":
            findings.extend(analyze_python_file(path, r))
        else:
            findings.extend(analyze_heuristic_file(path, r, lang))

    findings.sort(key=lambda f: f.total_score(), reverse=True)
    if max_findings is not None:
        findings = findings[:max_findings]

    return AnalysisReport(root=str(r), findings=findings)
