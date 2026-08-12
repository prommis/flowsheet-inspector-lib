"""Validate a prommis-wrap action eval workspace."""

from __future__ import annotations

import argparse
import py_compile
import re
from pathlib import Path


EXPECTED_STEPS = (
    "build",
    "set_operating_conditions",
    "initialize",
    "set_solver",
    "solve_initial",
)

REQUIRED_SNIPPETS = (
    "from idaes_fi.structfs.fsrunner import FlowsheetRunner, Context",
    "from idaes_fi.structfs.common import Steps",
    "FlowsheetRunner()",
)


STRING_STEP_RE = re.compile(r"@\w+\.step\(\s*['\"]")
EXPLICIT_STEPS_RE = re.compile(r"FlowsheetRunner\s*\(\s*steps\s*=")


def has_step_decorator(source: str, step_name: str) -> bool:
    pattern = re.compile(rf"@\w+\.step\(\s*Steps\.{re.escape(step_name)}\s*\)")
    return bool(pattern.search(source))


def set_solver_has_unused_model(source: str) -> bool:
    match = re.search(
        r"def\s+set_solver\s*\([^)]*\)\s*:\s*(?P<body>.*?)(?=^@\w+\.step|^def\s+|\Z)",
        source,
        flags=re.DOTALL | re.MULTILINE,
    )
    if not match:
        return False
    body = match.group("body")
    return "m = ctx.model" in body or "m = context.model" in body


def validate_python_syntax(path: Path, failures: list[str]) -> None:
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as error:
        failures.append(f"{path.name} does not compile: {error.msg}")


def validate_workspace(workspace: Path, input_file: str, output_file: str) -> list[str]:
    failures: list[str] = []

    input_path = workspace / input_file
    output_path = workspace / output_file

    if not input_path.is_file():
        failures.append(f"Missing original input file: {input_file}")

    if not output_path.is_file():
        failures.append(f"Missing wrapped output file: {output_file}")
        return failures

    source = output_path.read_text(encoding="utf-8")
    validate_python_syntax(output_path, failures)

    for snippet in REQUIRED_SNIPPETS:
        if snippet not in source:
            failures.append(f"Missing required snippet: {snippet}")

    if EXPLICIT_STEPS_RE.search(source):
        failures.append("Runner must use bare FlowsheetRunner() without an explicit steps argument")

    if STRING_STEP_RE.search(source):
        failures.append("Step decorators must use Steps constants, not string literals")

    for step_name in EXPECTED_STEPS:
        if not has_step_decorator(source, step_name):
            failures.append(f"Missing @FS.step(Steps.{step_name}) decorator")

    if set_solver_has_unused_model(source):
        failures.append("set_solver must not include unused m = ctx.model")

    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate prommis-wrap output.")
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--input-file", default="methanol_flowsheet.py")
    parser.add_argument("--output-file", default="methanol_flowsheet_w3.py")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failures = validate_workspace(args.workspace, args.input_file, args.output_file)

    if failures:
        print("FAIL prommis-wrap validation")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASS prommis-wrap validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
