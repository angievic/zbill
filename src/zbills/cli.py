from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from zbills import __version__
from zbills.analyzer import analyze_project
from zbills.llm.config import load_llm_config
from zbills.llm.enrich import enrich_findings
from zbills.llm.runtime import LLMSetupError, prepare_llm
from zbills.html_report import write_runtime_html
from zbills.report import format_console, write_json, write_markdown
from zbills.run_id import unique_zbill_runtime_dir_name

INIT_SNIPPET = """# ZBILLS — configuración sugerida
# Añade tu agent id y endpoint de ingest según tu SDK.

ZBILLS_AGENT_ID=
ZBILLS_API_KEY=

# --- LLM (analyze --llm) ---
# Proveedor: ollama | openai | anthropic | gemini
# Por defecto: ollama + mistral (local, bueno para código)
ZBILLS_LLM_PROVIDER=ollama
ZBILLS_LLM_MODEL=mistral

# Claves (según proveedor; solo la que uses)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=

# Ollama
OLLAMA_HOST=http://127.0.0.1:11434
"""


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    root.mkdir(parents=True, exist_ok=True)
    env_path = root / ".zbills.env.example"
    if not env_path.exists():
        env_path.write_text(INIT_SNIPPET, encoding="utf-8")
    print(f"Created {env_path}")
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    t0 = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()

    report = analyze_project(root, max_findings=args.max)

    if args.llm:
        try:
            cfg = load_llm_config(
                provider=args.provider,
                model=args.model,
            )
            prepare_llm(cfg)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
        except LLMSetupError as e:
            print(str(e), file=sys.stderr)
            return 2
        enrich_findings(root, report.findings, cfg, top_n=args.llm_top)
        report.llm = {
            "enabled": True,
            "provider": cfg.provider,
            "model": cfg.model,
            "enriched_top": args.llm_top,
        }

    parent_out = root if args.output_dir is None else Path(args.output_dir).resolve()
    parent_out.mkdir(parents=True, exist_ok=True)
    run_name = unique_zbill_runtime_dir_name()
    out_dir = (parent_out / run_name).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    finished_at = datetime.now(timezone.utc).isoformat()
    duration_s = round(time.perf_counter() - t0, 3)
    report.runtime = {
        "run_id": run_name,
        "run_folder": str(out_dir),
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_s,
        "zbills_version": __version__,
        "analyzed_root": str(root),
        "max_findings": args.max,
        "llm_enabled": bool(args.llm),
    }

    json_path = out_dir / "zbills_report.json"
    md_path = out_dir / "zbills_suggestions.md"
    html_path = out_dir / "zbills_runtime_report.html"
    write_json(report, json_path)
    write_markdown(report, md_path)
    write_runtime_html(report, html_path)

    print(format_console(report))
    print(f"Run folder: {out_dir}")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote {html_path}")
    return 0


def _find_report_json(root: Path) -> Path | None:
    direct = root / "zbills_report.json"
    if direct.is_file():
        return direct
    candidates = sorted(
        root.glob("**/*-zbill-runtime/zbills_report.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def cmd_suggest(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    json_path = _find_report_json(root)
    if json_path is None:
        print(
            "No zbills_report.json — run: zbills analyze . "
            "(o indica la carpeta *-zbill-runtime)",
            file=sys.stderr,
        )
        return 1
    data = json.loads(json_path.read_text(encoding="utf-8"))
    print(f"Using report: {json_path}", file=sys.stderr)
    for item in data.get("findings", [])[: args.limit]:
        print(f"\n{item['file']}::{item['function']} (line {item['line']})")
        for s in item.get("suggestions", []):
            print(f"  • {s['metric']}: {s['example']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="zbills",
        description="ZBILLS Analyzer — sugiere dónde instrumentar métricas ROI",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Crea .zbills.env.example en el proyecto")
    p_init.add_argument("path", nargs="?", default=".", help="Directorio del proyecto")
    p_init.set_defaults(func=cmd_init)

    p_an = sub.add_parser("analyze", help="Escanea el repo y genera reportes")
    p_an.add_argument("path", nargs="?", default=".", help="Raíz del repositorio")
    p_an.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Directorio padre donde crear la carpeta *-zbill-runtime (default: raíz analizada)",
    )
    p_an.add_argument(
        "--max",
        type=int,
        default=None,
        help="Máximo de hallazgos (ranking por score)",
    )
    p_an.add_argument(
        "--llm",
        action="store_true",
        help="Enriquecer hallazgos con LLM (Gemini, OpenAI, Claude u Ollama vía env/flags)",
    )
    p_an.add_argument(
        "--provider",
        default=None,
        help="ollama | openai | anthropic | gemini (override a ZBILLS_LLM_PROVIDER)",
    )
    p_an.add_argument(
        "--model",
        default=None,
        help="Override a ZBILLS_LLM_MODEL (p. ej. mistral, gpt-4o-mini, claude-3-5-sonnet-20241022)",
    )
    p_an.add_argument(
        "--llm-top",
        type=int,
        default=15,
        metavar="N",
        help="Cuántos hallazgos (desde el ranking) enviar al LLM",
    )
    p_an.set_defaults(func=cmd_analyze)

    p_su = sub.add_parser("suggest", help="Muestra ejemplos track() desde zbills_report.json")
    p_su.add_argument("path", nargs="?", default=".", help="Directorio con zbills_report.json")
    p_su.add_argument("--limit", type=int, default=20)
    p_su.set_defaults(func=cmd_suggest)

    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
