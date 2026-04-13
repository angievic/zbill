from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Suggestion:
    metric: str
    category: str  # "impact" | "cost"
    reason: str
    suggestion: str  # código zbills.track(...)
    score: float = 0.0
    fields: dict[str, list[str]] | None = None  # required / optional keys

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "metric": self.metric,
            "category": self.category,
            "reason": self.reason,
            "suggestion": self.suggestion,
            "score": round(self.score, 2),
        }
        if self.fields:
            d["fields"] = {
                "required": list(self.fields.get("required", [])),
                "optional": list(self.fields.get("optional", [])),
            }
        d["example"] = self.suggestion  # compat
        return d

    @property
    def example(self) -> str:
        """Alias retrocompatible."""
        return self.suggestion


@dataclass
class Finding:
    file: str
    function: str
    line: int
    language: str
    suggestions: list[Suggestion] = field(default_factory=list)
    llm: dict[str, Any] | None = None

    def total_score(self) -> float:
        return sum(s.score for s in self.suggestions)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "file": self.file,
            "function": self.function,
            "line": self.line,
            "language": self.language,
            "suggestions": [s.to_dict() for s in self.suggestions],
        }
        if self.llm is not None:
            d["llm"] = self.llm
        return d


@dataclass
class AnalysisReport:
    root: str
    findings: list[Finding] = field(default_factory=list)
    llm: dict[str, Any] | None = None
    runtime: dict[str, Any] | None = None

    def sorted_findings(self) -> list[Finding]:
        return sorted(self.findings, key=lambda f: f.total_score(), reverse=True)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "root": self.root,
            "count": len(self.findings),
            "findings": [f.to_dict() for f in self.sorted_findings()],
        }
        if self.llm is not None:
            d["llm"] = self.llm
        if self.runtime is not None:
            d["runtime"] = self.runtime
        return d
