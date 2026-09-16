from __future__ import annotations
import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from . import __version__
from .storage import Store, default_db
from .ingest import import_path
from .analytics import analyze, mine_workflows
from .audit import audit_instructions, audit_plan, load_files
from .demo import demo_messages
from .reports import public_analysis, report_markdown, report_html, report_csv
from .prompt_library import get_prompt
from .provider import capabilities


def write_or_print(text: str, out: str | None):
    if out:
        path = Path(out).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(f"Written: {path.resolve()}")
    else:
        print(text)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="codex-evolution", description="Local-first Codex history analytics, instruction audits and Skill drafts.")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--db", default=str(default_db()), help="Application-owned SQLite database (not a Codex database).")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("demo", "serve"):
        p = sub.add_parser(name, help="Start local web UI with " + ("synthetic demo data." if name == "demo" else "imported history."))
        p.add_argument("--port", type=int, default=8765)
        p.add_argument("--tz", default="UTC")
        p.add_argument("--open", action="store_true", help="Open browser after startup.")
    p = sub.add_parser("import", help="Import an explicit CODEX_HOME, history/rollout JSONL, or normalized JSON file.")
    p.add_argument("path")
    p = sub.add_parser("report", help="Export deterministic, aggregate-only report.")
    p.add_argument("--format", choices=["md", "json", "html", "csv"], default="md")
    p.add_argument("--out")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--from", dest="start", default="")
    p.add_argument("--to", dest="end", default="")
    p.add_argument("--project", default="")
    p.add_argument("--tz", default="UTC")
    p = sub.add_parser("audit", help="Propose instruction/plan changes; NEVER modifies the input.")
    p.add_argument("path")
    p.add_argument("--plan", action="store_true", help="Audit a plain-text project plan rather than instruction files.")
    p.add_argument("--out", help="Write JSON findings to a separate output file.")
    p = sub.add_parser("skills", help="Mine repeated prompt-stage patterns; export uninstalled Skill drafts.")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--out", help="Explicit directory for review drafts (nothing is installed automatically).")
    p.add_argument("--tz", default="UTC")
    p = sub.add_parser("prompt", help="Print a complete Codex-ready review prompt.")
    p.add_argument("name", choices=["retrospective", "anti-bloat", "instruction-audit", "workflow-to-skill", "checkpoint"])
    p.add_argument("--out")
    sub.add_parser("doctor", help="Show runtime/config status without reading history or credentials.")
    args = parser.parse_args(argv)
    try:
        if args.command == "prompt":
            write_or_print(get_prompt(args.name), args.out)
            return
        if args.command == "doctor":
            print(json.dumps({"version": __version__, "python": sys.version.split()[0], "database": str(Path(args.db).expanduser()),
                              "codex_cli": shutil.which("codex"), "codex_home": os.environ.get("CODEX_HOME", "~/.codex"),
                              "optional_model": capabilities(), "runtime_dependencies": []}, ensure_ascii=False, indent=2))
            return
        if args.command == "audit":
            if args.out and Path(args.out).expanduser().resolve() == Path(args.path).expanduser().resolve():
                raise ValueError("Audit output must not overwrite its input.")
            if args.plan:
                result = audit_plan(Path(args.path).expanduser().read_text(encoding="utf-8"))
            else:
                files, warnings = load_files(args.path)
                if not files:
                    raise ValueError("No instruction files found.")
                result = audit_instructions(files)
                result["limitations"].extend(warnings)
                if args.out and Path(args.out).name in {"AGENTS.md", "AGENTS.override.md", "SKILL.md"}:
                    raise ValueError("Write the JSON report to a separate .json output, never an instruction file.")
            write_or_print(json.dumps(result, ensure_ascii=False, indent=2), args.out)
            return
        store = Store(args.db)
        if args.command in {"demo", "serve"}:
            from .server import serve
            serve(store, port=args.port, mode="demo" if args.command == "demo" else "live", timezone=args.tz, open_browser=args.open)
        elif args.command == "import":
            result = store.ingest(import_path(args.path))
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.command == "report":
            rows = demo_messages() if args.demo else store.messages()
            data = analyze(rows, start=args.start, end=args.end, project=args.project, tz=args.tz, mode="demo" if args.demo else "live")
            renderers = {"md": report_markdown, "html": report_html, "csv": report_csv,
                         "json": lambda d: json.dumps(public_analysis(d), ensure_ascii=False, indent=2)}
            write_or_print(renderers[args.format](data), args.out)
        elif args.command == "skills":
            candidates = mine_workflows(demo_messages() if args.demo else store.messages(), tz=args.tz)
            if args.out:
                base = Path(args.out).expanduser()
                base.mkdir(parents=True, exist_ok=True)
                for c in candidates:
                    folder = base / c["id"]
                    folder.mkdir(exist_ok=True)
                    target = folder / "SKILL.md"
                    if target.exists():
                        raise ValueError(f"Review draft already exists; refusing to overwrite {target}.")
                    target.write_text(c["skill"], encoding="utf-8")
                print(f"Created {len(candidates)} review drafts in {base.resolve()}. No skills were installed.")
            else:
                print(json.dumps(candidates, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Error: {exc}\n")
