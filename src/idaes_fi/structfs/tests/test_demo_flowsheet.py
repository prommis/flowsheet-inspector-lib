#################################################################################
# Process Optimization and Modeling for Minerals Sustainability (PrOMMiS) Copyright (c) 2023-2026
#
# “Process Optimization and Modeling for Minerals Sustainability (PrOMMiS)” was produced under the DOE
# Process Optimization and Modeling for Minerals Sustainability (“PrOMMiS”) initiative, and is
# copyrighted by the software owners: The Regents of the University of California, through Lawrence
# Berkeley National Laboratory, National Technology & Engineering Solutions of Sandia, LLC through
# Sandia National Laboratories, Carnegie Mellon University, University of Notre Dame, and West
# Virginia University Research Corporation.
#
# NOTICE. This Software was developed under funding from the U.S. Department of Energy and the
# U.S. Government consequently retains certain rights. As such, the U.S. Government has been granted
# for itself and others acting on its behalf a paid-up, nonexclusive, irrevocable, worldwide license
# in the Software to reproduce, distribute copies to the public, prepare derivative works, and perform
# publicly and display publicly, and to permit other to do so.
#
#################################################################################
"""
Tests that utilize the demo_flowsheet_structured.py module in this
directory.
"""

# stdlib
from pathlib import Path

# third-party
import pytest

# package
from ..runner import ReportDB
from .demo_flowsheet_structured import FS
from .demo_flowsheet_fi_main import main
from ..common import ActionNames
from idaes_fi.gitutil import git_head_hash


@pytest.mark.unit
def test_fs_ok():
    assert FS is not None
    assert hasattr(FS, "run_steps")


@pytest.mark.integration
def test_fs_run_steps(tmp_path):

    dbpath = tmp_path / "test_fs_run_steps.db"
    FS.set_report_db(dbfile=dbpath)
    FS.run_steps()
    db = FS.get_report_db()
    assert Path(db._filename) == dbpath

    _check_report_ok(db)


@pytest.mark.integration
def test_fi_main(tmp_path):
    dbpath = tmp_path / "test_fs_run_steps.db"
    main(dbfile=dbpath)

    db = ReportDB(dbpath)
    assert Path(db._filename) == dbpath

    _check_report_ok(db)


def _check_report_ok(db):
    rpt = db.get_last_report()
    assert rpt
    actions = rpt["actions"]
    last_solve = actions[ActionNames.SOLVER_RESULTS.value]["results"][-1]["solver"]
    print(last_solve)
    assert last_solve["Status"] == "ok"
    assert last_solve["Termination condition"] == "optimal"

    last_row = db.get_last_meta()
    assert last_row
    print(f"last row: {last_row}")
    assert last_row["name"] == "Demo Flowsheet"
    assert bool(last_row["run_status"]) == True

    _check_git_hash_report(actions[ActionNames.GIT_HASH.value])


def _check_git_hash_report(data):
    caller_file = Path(__file__)
    rpt_hash = data["hash"]
    caller_hash = git_head_hash(caller_file)
    assert rpt_hash == caller_hash
