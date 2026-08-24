"""
test_purity.py — enforces that core/ is harness-blind.

Walks every .py file under core/ (excluding this tests/ directory itself),
parses each file with the ast module, and fails if any module-level or
local import touches a banned namespace: agent, dashboard, trueforge, mcp,
fastapi, uvicorn, pydantic, httpx, requests, aiohttp, or dotenv.

This test must stay real — not a stub — because it is the only automated
mechanism keeping the core/agent boundary clean under deadline pressure.
If it is ever weakened, the isolation guarantee disappears silently.
"""

import ast
import pathlib

CORE_ROOT = pathlib.Path(__file__).parent.parent

# directories to skip — only the tests package itself
EXCLUDED_DIRS = {"tests"}

# top-level module prefixes that must never appear in core/ imports
BANNED_PREFIXES = (
    "agent",
    "dashboard",
    "trueforge",
    "mcp",
    "fastapi",
    "uvicorn",
    "pydantic",
    "httpx",
    "requests",
    "aiohttp",
    "dotenv",
)


def _collect_core_files() -> list[pathlib.Path]:
    """Return all .py files under core/ excluding the tests/ subdirectory."""
    files = []
    for p in CORE_ROOT.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in p.relative_to(CORE_ROOT).parts):
            continue
        files.append(p)
    return files


def _banned_imports_in_file(path: pathlib.Path) -> list[str]:
    """
    Parse the file at *path* and return a list of banned import strings found.
    Checks both 'import X' and 'from X import Y' nodes at any nesting depth.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BANNED_PREFIXES:
                    found.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            root = node.module.split(".")[0]
            if root in BANNED_PREFIXES:
                found.append(f"from {node.module} import ...")
    return found


def test_core_has_no_banned_imports() -> None:
    """Every .py in core/ (outside tests/) must import only stdlib and numpy."""
    core_files = _collect_core_files()
    assert core_files, "No core/ files found — check CORE_ROOT path"

    violations: dict[str, list[str]] = {}
    for f in core_files:
        bad = _banned_imports_in_file(f)
        if bad:
            violations[str(f.relative_to(CORE_ROOT))] = bad

    if violations:
        lines = ["core/ purity violation — banned imports found:"]
        for filename, imports in violations.items():
            for imp in imports:
                lines.append(f"  {filename}: {imp}")
        raise AssertionError("\n".join(lines))
