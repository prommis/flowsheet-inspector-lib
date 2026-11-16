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
Tests for the `fi-db` command-line tool (`idaes_fi.db_tools`).
"""

import pytest

from ..reportdb import ReportDB
from .. import db_tools


@pytest.fixture
def populated_db(tmp_path):
    """A report DB with two records, for exercising the `fi-db` commands."""
    dbfile = tmp_path / "fidb_test.sqlite"
    db = ReportDB(str(dbfile)).create(exist_ok=True)
    db.set_target(module="m", filedir="/some/dir", filename="flowsheet.py", hash="h")
    db.add_report(
        {"a": 1}, tags="alpha beta", name="run_one", run_status=True, solver_status="ok"
    )
    db.add_report(
        {"b": 2},
        tags="gamma",
        name="run_two",
        run_status=False,
        solver_status="warning",
    )
    return str(dbfile)


@pytest.mark.unit
def test_info_command(populated_db, capfd):
    """`fi-db info` prints the record count and database summary."""
    assert db_tools.main(["info", "--db", populated_db]) == 0
    out = capfd.readouterr().out
    assert "Database file" in out
    assert "Number of records" in out
    assert "2" in out  # two records


@pytest.mark.unit
def test_view_command(populated_db, capfd):
    """`fi-db view` lists all records with the combined file column."""
    assert db_tools.main(["view", "--db", populated_db]) == 0
    out = capfd.readouterr().out
    assert "run_one" in out
    assert "run_two" in out
    # filedir + filename are combined into a single `file` column
    assert "flowsheet.py" in out


@pytest.mark.unit
def test_view_name_fixed(populated_db, capfd):
    """`--name_fixed` filters records by exact name."""
    assert db_tools.main(["view", "--db", populated_db, "--name_fixed", "run_one"]) == 0
    out = capfd.readouterr().out
    assert "run_one" in out
    assert "run_two" not in out


@pytest.mark.unit
def test_view_name_regex(populated_db, capfd):
    """`--name_re` filters records by a regular expression on name."""
    assert db_tools.main(["view", "--db", populated_db, "--name_re", "run_t.*"]) == 0
    out = capfd.readouterr().out
    assert "run_two" in out
    assert "run_one" not in out


@pytest.mark.unit
def test_view_tags(populated_db, capfd):
    """`--tags` filters records by tag."""
    assert db_tools.main(["view", "--db", populated_db, "--tags", "alpha"]) == 0
    out = capfd.readouterr().out
    assert "run_one" in out
    assert "run_two" not in out


@pytest.mark.unit
def test_view_time_range(populated_db, capfd):
    """`--time_min`/`--time_max` filter records by creation time range."""
    assert (
        db_tools.main(
            [
                "view",
                "--db",
                populated_db,
                "--time_min",
                "2000-01-01",
                "--time_max",
                "2100-01-01",
            ]
        )
        == 0
    )
    out = capfd.readouterr().out
    assert "run_one" in out


@pytest.mark.unit
def test_view_bad_time_min(populated_db, capfd):
    """A non-ISO `--time_min` reports an error and exits non-zero."""
    assert db_tools.main(["view", "--db", populated_db, "--time_min", "nope"]) != 0
    assert "ERROR" in capfd.readouterr().out


@pytest.mark.unit
def test_view_bad_time_max(populated_db, capfd):
    """A non-ISO `--time_max` reports an error and exits non-zero."""
    assert db_tools.main(["view", "--db", populated_db, "--time_max", "nope"]) != 0
    assert "ERROR" in capfd.readouterr().out


@pytest.mark.unit
def test_view_bad_regex(populated_db, capfd):
    """An invalid `--name_re` regex reports an error and exits non-zero."""
    assert db_tools.main(["view", "--db", populated_db, "--name_re", "["]) != 0
    assert "ERROR" in capfd.readouterr().out


@pytest.mark.unit
def test_info_uninitialized_db(tmp_path, capfd):
    """`fi-db info` on an uninitialized DB reports an error and exits non-zero."""
    # a valid SQLite file that has not been initialized as a report DB
    # (no `version` table) -> DBError -> CommandError -> non-zero exit
    import sqlite3

    empty = tmp_path / "empty.sqlite"
    sqlite3.connect(str(empty)).close()
    assert db_tools.main(["info", "--db", str(empty)]) != 0
    assert "ERROR" in capfd.readouterr().out


@pytest.mark.unit
def test_verbose_and_quiet_flags(populated_db, capfd):
    """The `-v`/`-q` logging flags are accepted by the commands."""
    # exercise the logging-setup branches
    assert db_tools.main(["info", "--db", populated_db, "-vv"]) == 0
    capfd.readouterr()
    assert db_tools.main(["info", "--db", populated_db, "-q"]) == 0
