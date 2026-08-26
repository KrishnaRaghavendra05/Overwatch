import ast
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# local qodo & purity checker: validates changes before pr filing
# checks core purity, scale discipline, logging, and single-write gate

REPO_ROOT = Path(__file__).parent.parent
BANNED_CORE_PREFIXES = (
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


# verify core modules only import stdlib and numpy
def check_core_purity() -> list[str]:
    violations = []
    core_dir = REPO_ROOT / "core"
    for py_file in core_dir.rglob("*.py"):
        if "tests" in py_file.parts:
            continue
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in BANNED_CORE_PREFIXES:
                        rel = py_file.relative_to(REPO_ROOT)
                        violations.append(f"{rel}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root = node.module.split(".")[0]
                    if root in BANNED_CORE_PREFIXES:
                        rel = py_file.relative_to(REPO_ROOT)
                        violations.append(f"{rel}: from {node.module} import ...")
    return violations


# verify only approval_gate.py imports dashboard.write
def check_dashboard_write_boundary() -> list[str]:
    violations = []
    allowed_file = (
        REPO_ROOT / "agent" / "workflow" / "approval_gate.py"
    ).resolve()
    for py_file in REPO_ROOT.rglob("*.py"):
        if py_file.resolve() == allowed_file:
            continue
        parts = py_file.parts
        if "tests" in parts or "dashboard" in parts or ".venv" in parts:
            continue
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
        for node in ast.walk(tree):
            rel = py_file.relative_to(REPO_ROOT)
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module == "dashboard.write":
                    violations.append(f"{rel}: forbidden import of dashboard.write")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "dashboard.write":
                        violations.append(f"{rel}: forbidden import of dashboard.write")
    return violations


# verify no bare print statements in agent or core
def check_no_print_statements() -> list[str]:
    violations = []
    for folder in ["core", "agent", "dashboard"]:
        target_dir = REPO_ROOT / folder
        for py_file in target_dir.rglob("*.py"):
            if "tests" in py_file.parts:
                continue
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "print"
                ):
                    rel = py_file.relative_to(REPO_ROOT)
                    violations.append(
                        f"{rel}:L{node.lineno} uses print() instead of logging"
                    )
    return violations


# run all local qodo rule checks
def run_qodo_checks() -> bool:
    logging.info("Running Qodo Repository Rule Verification...")
    passed = True

    purity_issues = check_core_purity()
    if purity_issues:
        passed = False
        logging.error("Purity Violations in core/:")
        for issue in purity_issues:
            logging.error("  %s", issue)
    else:
        logging.info("Architecture Purity Check: PASS (core/ is harness-blind)")

    write_issues = check_dashboard_write_boundary()
    if write_issues:
        passed = False
        logging.error("Write Boundary Violations:")
        for issue in write_issues:
            logging.error("  %s", issue)
    else:
        logging.info(
            "Safety Gate Check: PASS (only approval_gate imports dashboard.write)"
        )

    print_issues = check_no_print_statements()
    if print_issues:
        passed = False
        logging.error("Logging Violations (found bare print calls):")
        for issue in print_issues:
            logging.error("  %s", issue)
    else:
        logging.info("Structured Logging Check: PASS (0 bare print calls)")

    # Check if pr_agent CLI is available in PATH or python module
    if os.environ.get("OPENAI_KEY") or os.environ.get("QODO_API_KEY"):
        logging.info("Qodo API Key detected in environment.")
        try:
            res = subprocess.run(
                [sys.executable, "-m", "pr_agent.cli", "--help"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                logging.info("pr-agent CLI is installed and ready for local runs.")
        except Exception:
            pass

    return passed


if __name__ == "__main__":
    ok = run_qodo_checks()
    sys.exit(0 if ok else 1)
