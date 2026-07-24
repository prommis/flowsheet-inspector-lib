#!/usr/bin/env python3
"""Verify that expected imports occur exactly once in a Python file.

Usage:
    python verify_file_imports.py FILE MODULE CLASS [MODULE CLASS ...]

The target file is parsed but never executed, so this check cannot build or
solve a flowsheet as a side effect.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from pathlib import Path
import sys
from typing import Sequence


class ImportVerificationError(ValueError):
    """Raised when a file does not contain the expected imports."""


def verify_file_imports(
    file_path: str | Path,
    expected_imports: Sequence[tuple[str, str]],
) -> None:
    """Verify syntax and exact, unaliased, top-level imports in file_path."""
    path = Path(file_path)
    if not path.is_file():
        raise ImportVerificationError(f"File not found: {path}")
    if not expected_imports:
        raise ImportVerificationError("At least one expected import is required.")

    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as err:
        raise ImportVerificationError(f"File is not valid UTF-8: {path}") from err

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as err:
        location = f"line {err.lineno}" if err.lineno is not None else "unknown line"
        raise ImportVerificationError(
            f"Python syntax error in {path} at {location}: {err.msg}"
        ) from err

    counts: Counter[tuple[str, str]] = Counter()
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.level != 0 or node.module is None:
            continue
        for imported_name in node.names:
            if imported_name.asname is None:
                counts[(node.module, imported_name.name)] += 1

    problems = []
    for module_name, class_name in expected_imports:
        count = counts[(module_name, class_name)]
        statement = f"from {module_name} import {class_name}"
        if count == 0:
            problems.append(f"missing: {statement}")
        elif count > 1:
            problems.append(f"duplicated {count} times: {statement}")

    if problems:
        raise ImportVerificationError("; ".join(problems))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify exact imports in a Python file without executing it."
    )
    parser.add_argument("file", help="Python file to inspect")
    parser.add_argument(
        "expected",
        nargs="+",
        metavar="MODULE_OR_CLASS",
        help="One or more MODULE CLASS pairs",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if len(args.expected) % 2:
        parser.error("expected imports must be supplied as MODULE CLASS pairs")

    expected_imports = list(zip(args.expected[::2], args.expected[1::2]))
    try:
        verify_file_imports(args.file, expected_imports)
    except ImportVerificationError as err:
        print(f"Verification failed: {err}", file=sys.stderr)
        return 1

    print(f"Verified {len(expected_imports)} import(s) in {args.file}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
