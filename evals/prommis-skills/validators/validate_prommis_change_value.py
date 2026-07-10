"""Validate a prommis-change-value action eval workspace."""

from __future__ import annotations

import argparse
import py_compile
from pathlib import Path


OLD_VALUE = "m.fs.R101.conversion.fix(0.75 * pyunits.dimensionless)"
NEW_VALUES = (
    "m.fs.R101.conversion.fix(0.80 * pyunits.dimensionless)",
    "m.fs.R101.conversion.fix(0.8 * pyunits.dimensionless)",
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

    if not any(value in source for value in NEW_VALUES):
        failures.append("The reactor conversion was not changed to 0.80.")

    if OLD_VALUE in source:
        failures.append("The original reactor conversion value 0.75 is still present.")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()

    failures = validate_workspace(args.workspace, args.output_file)

    if failures:
        print("FAIL prommis-change-value validation")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASS prommis-change-value validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
