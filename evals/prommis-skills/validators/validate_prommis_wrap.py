"""Validate a prommis-wrap action eval workspace."""

from __future__ import annotations

import argparse
import py_compile
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
    "FlowsheetRunner",
    "steps=",
)


def has_step_decorator(source: str, step_name: str) -> bool:
    double_quoted = f'@FS.step("{step_name}")'
    single_quoted = f"@FS.step('{step_name}')"
    return double_quoted in source or single_quoted in source


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

    for step_name in EXPECTED_STEPS:
        if not has_step_decorator(source, step_name):
            failures.append(f"Missing @FS.step decorator for: {step_name}")

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
