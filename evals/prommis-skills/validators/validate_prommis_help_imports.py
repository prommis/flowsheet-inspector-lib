"""Validate a prommis-help-imports action eval workspace."""

from __future__ import annotations

import argparse
import py_compile
from pathlib import Path


ACCEPTED_IMPORTS = (
    "from idaes.core import FlowsheetBlock",
    "from idaes.core.base.flowsheet_model import FlowsheetBlock",
)


def check_python_syntax(path: Path, failures: list[str]) -> None:
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as error:
        failures.append(f"{path.name} does not compile: {error.msg}")


def validate_workspace(workspace: Path, output_file: str) -> list[str]:
    failures: list[str] = []
    target_path = workspace / output_file

    if not target_path.is_file():
        return [f"Missing target file: {output_file}"]

    source = target_path.read_text(encoding="utf-8")
    check_python_syntax(target_path, failures)

    if not any(import_line in source for import_line in ACCEPTED_IMPORTS):
        failures.append("The correct FlowsheetBlock import was not added.")

    if "FlowsheetBlock(dynamic=False)" not in source:
        failures.append("The original FlowsheetBlock usage was not preserved.")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()

    failures = validate_workspace(args.workspace, args.output_file)

    if failures:
        print("FAIL prommis-help-imports validation")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASS prommis-help-imports validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
