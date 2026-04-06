from __future__ import annotations

import os
from pathlib import Path

DEFAULT_IGNORE_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        "node_modules",
        "venv",
        ".venv",
        ".tox",
        "dist",
        "build",
        ".eggs",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "vendor",
        "target",  # Rust / some Java
    }
)

LANG_BY_EXT: dict[str, str] = {
    ".py": "python",
    ".go": "go",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".rb": "ruby",
}


def should_skip_dir(name: str) -> bool:
    if name in DEFAULT_IGNORE_DIRS:
        return True
    if name.endswith(".egg-info"):
        return True
    return False


def iter_source_files(root: Path) -> list[tuple[Path, str]]:
    out: list[tuple[Path, str]] = []
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]
        base = Path(dirpath)
        for fn in filenames:
            ext = Path(fn).suffix.lower()
            lang = LANG_BY_EXT.get(ext)
            if lang:
                out.append((base / fn, lang))
    return out
