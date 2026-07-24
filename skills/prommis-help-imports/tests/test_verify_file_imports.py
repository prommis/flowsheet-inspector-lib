import sys
from pathlib import Path

import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from verify_file_imports import ImportVerificationError, verify_file_imports


EXPECTED_IMPORTS = [
    ("pyomo.network", "Arc"),
    ("idaes.core", "FlowsheetBlock"),
]


def write_python_file(tmp_path: Path, source: str) -> Path:
    path = tmp_path / "flowsheet.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_accepts_expected_imports(tmp_path):
    path = write_python_file(
        tmp_path,
        "from pyomo.network import Arc\n"
        "from idaes.core import FlowsheetBlock\n",
    )

    verify_file_imports(path, EXPECTED_IMPORTS)


def test_accepts_import_in_group(tmp_path):
    path = write_python_file(
        tmp_path,
        "from idaes.core import FlowsheetBlock, UnitModelCostingBlock\n"
        "from pyomo.network import Arc\n",
    )

    verify_file_imports(path, EXPECTED_IMPORTS)


def test_rejects_missing_import(tmp_path):
    path = write_python_file(tmp_path, "from pyomo.network import Arc\n")

    with pytest.raises(ImportVerificationError, match="missing"):
        verify_file_imports(path, EXPECTED_IMPORTS)


def test_rejects_duplicate_import(tmp_path):
    path = write_python_file(
        tmp_path,
        "from pyomo.network import Arc\n"
        "from pyomo.network import Arc\n"
        "from idaes.core import FlowsheetBlock\n",
    )

    with pytest.raises(ImportVerificationError, match="duplicated 2 times"):
        verify_file_imports(path, EXPECTED_IMPORTS)


def test_rejects_aliased_import(tmp_path):
    path = write_python_file(
        tmp_path,
        "from pyomo.network import Arc as NetworkArc\n"
        "from idaes.core import FlowsheetBlock\n",
    )

    with pytest.raises(ImportVerificationError, match="missing"):
        verify_file_imports(path, EXPECTED_IMPORTS)


def test_rejects_syntax_error(tmp_path):
    path = write_python_file(
        tmp_path,
        "from pyomo.network import Arc\n"
        "from idaes.core import FlowsheetBlock\n"
        "def broken(:\n",
    )

    with pytest.raises(ImportVerificationError, match="syntax error"):
        verify_file_imports(path, EXPECTED_IMPORTS)
