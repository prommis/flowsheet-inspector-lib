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
Tests for the Progress action.
"""

from types import SimpleNamespace
import sqlite3

import pytest

from idaes_fi.api import FlowsheetRunner, Steps
from idaes_fi.reportdb import ReportDB
from idaes_fi.actions.progress import Progress, Status, StepInfo
from idaes_fi.tests import demo_flowsheet


@pytest.fixture
def runner():
    r = SimpleNamespace()
    r.report_db = SimpleNamespace()
    r.report_db.add_status = lambda *args, **kwargs: capture_add_status(
        r, *args, **kwargs
    )
    r.report_db.get_last_run_id = lambda: 1
    r._reportdb = r.report_db
    r._status_calls = []  # reset for each test
    return r


def capture_add_status(*args, **kwargs):
    print(f"add_status called with args={args}, kwargs={kwargs}")
    runner = args[0] if args else None
    if runner is not None and hasattr(runner, "_status_calls"):
        runner._status_calls.append((args, kwargs))


def get_last_status_kw(runner):
    print(
        f"status calls: {runner._status_calls if hasattr(runner, '_status_calls') else 'none'}"
    )
    if hasattr(runner, "_status_calls") and runner._status_calls:
        return runner._status_calls[-1][1]
    return None


@pytest.mark.unit
def test_progress_smoke(runner):
    p = Progress(runner)
    si = StepInfo(name="foo", number=1, status=Status.RUNNING, start=0.0)


@pytest.mark.unit
def test_progress_api(runner):
    p = Progress(runner)
    p.before_run()
    p.before_step("step1")
    p.before_step("solve_step")  # will trigger solver logic
    p.before_step("step3")
    p.after_run()


@pytest.mark.integration
def test_progress_flowsheet(tmp_path):
    db = tmp_path / "report.sqlite"
    runner = demo_flowsheet.f1_runner
    runner.report_db_file = db
    save_main = runner.main
    try:
        runner.main = progress_main
        print(f"run demo flowsheet with temp db '{db}'")
        runner.run_flowsheet()  # rest of checks are in this function
    finally:
        # need to reset since this is a global object
        runner.main = save_main


def progress_main(runner: FlowsheetRunner):
    # check that the run id is set in the actions
    rid = None
    for a in runner.actions:
        assert a.run_id is not None
        if rid is None:
            rid = a.run_id
        else:
            # they should all be the same
            assert rid == a.run_id
    # do build step
    runner.step_begin(Steps.build)
    runner.model = demo_flowsheet.build_flowsheet()
    # end build step (start next)
    runner.step_begin(Steps.set_scaling)
    # double-check that run id is still the same
    for a in runner.actions:
        assert a.run_id is not None
        assert rid == a.run_id
    # there should be a single row in the status table
    # with this run id
    with sqlite3.connect(runner.report_db_file) as conn:
        n = 0
        for row in conn.execute(f"SELECT * FROM {ReportDB.STAT_TABLE}"):
            assert n == 0  # should not be > 1 row
            run_id = row[1]
            assert run_id == rid
            n += 1
    # start another step (end 2nd step)
    runner.step_begin(Steps.initialize)
    # now there should be 2 rows with that run id
    with sqlite3.connect(runner.report_db_file) as conn:
        n = 0
        for row in conn.execute(f"SELECT * FROM {ReportDB.STAT_TABLE}"):
            assert n < 2
            run_id = row[1]
            assert run_id == rid
            n += 1

    # that's it, we're done!


def test_progress_solve_status(runner):

    p = Progress(runner)

    # solve optimal
    p.before_run()
    p.before_step("solve_step")
    # simulate optimal solve
    runner.optimal = True
    p.after_step("solve_step")
    assert p._step_info[-1].solve_ok is True
    # check status that would have been added to DB
    status = get_last_status_kw(runner)
    assert status is not None and status["solve_ok"] is True

    # solve not optimal
    p.before_step("solve_step2")
    runner.optimal = False
    p.after_step("solve_step2")
    assert p._step_info[-1].solve_ok is False
    # check status that would have been added to DB
    status = get_last_status_kw(runner)
    assert status is not None and status["solve_ok"] is False

    # not a solve step
    p.before_step("non_solve_step")
    p.after_step("non_solve_step")
    assert p._step_info[-1].solve_ok is None
    status = get_last_status_kw(runner)
    assert status["solve_ok"] is None
