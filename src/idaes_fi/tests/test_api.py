######################################################################################################
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
######################################################################################################
"""
Tests for the idaes_fi API module.
"""

import logging
from pathlib import Path
import sys

import pytest

from idaes_fi import api
from idaes.logger import set_log_tags
from idaes_fi.tests import demo_flowsheet
from .shared import flowsheet_var

__author__ = "Dan Gunter (LBNL)"


@pytest.fixture
def tmpdb(tmp_path):
    return tmp_path / "reportdb.sqlite"


@pytest.mark.unit
def test_null():
    def say_hello(runner):
        return f"hello {runner}"

    runner = api.NullFlowsheetRunner()
    runner.main = say_hello
    runner.model = "not really a model"
    assert runner.model == "not really a model"
    result = runner.run_flowsheet()
    assert result == f"hello {runner}"


@pytest.mark.unit
def test_log_level():
    steps = ("a", "b")
    runner = api.FlowsheetRunner(steps=steps, report_db=False, quiet=True)

    def noop(runner):
        runner.step_begin("a")
        runner.model = demo_flowsheet.build_flowsheet()
        runner.step_begin("b")

    runner.main = noop
    runner.log_level = logging.INFO
    set_log_tags(("ui",))
    runner.run_flowsheet()


@pytest.mark.unit
def test_last_step(tmp_path):
    steps = ("a", "b", "c", "d")
    runner = api.FlowsheetRunner(steps=steps, report_db=tmp_path / "runner.db")
    where = None

    def mymain(runner):
        runner.step_begin("a")
        where.append("a")
        runner.model = demo_flowsheet.build_flowsheet()
        runner.step_begin("b")
        where.append("b")
        runner.step_begin("c")
        where.append("c")
        runner.step_begin("d")
        where.append("d")

    runner.main = mymain
    print("\nStep: ", end="")  # dbg
    sys.stdout.flush()
    for step_name in "abcd":
        print(f"{step_name}", end=" -> ")  # dbg
        sys.stdout.flush()
        where = []
        runner.last_step = step_name
        runner.run_flowsheet()
        assert where[-1] == step_name
    print("done.")


@pytest.mark.integration
@pytest.mark.parametrize(
    "quiet,report_db", [(True, True), (False, False), (True, False)]
)
def test_demo_flowsheet(tmp_path, quiet, report_db):
    print(f"quiet={quiet} report_db={report_db}")
    if report_db:
        report_db = tmp_path / "test_api_demo_flowsheet_db.sqlite"
    runner = api.FlowsheetRunner(
        steps=(
            api.Steps.build,
            api.Steps.set_scaling,
            api.Steps.initialize,
            api.Steps.set_solver,
            api.Steps.solve_optimization,
        ),
        report_db=report_db,
        quiet=quiet,
    )
    runner.main = fs_main
    runner.run_flowsheet()


def fs_main(runner):
    runner.step_begin(api.Steps.build)
    runner.model = m = demo_flowsheet.build_flowsheet()

    runner.step_begin(api.Steps.set_scaling)
    demo_flowsheet.set_scaling(m)
    runner.step_end()

    demo_flowsheet.set_dof(m)

    runner.step_begin(api.Steps.initialize)
    demo_flowsheet.initialize_flowsheet(m)

    runner.step_begin(api.Steps.set_solver)
    solver = demo_flowsheet.get_solver()

    runner.step_begin(api.Steps.solve_optimization)
    demo_flowsheet.solve_flowsheet(m, solver, stee=True)


# ----
# Tests for utility functions
# ----


@pytest.mark.unit
def test_get_module_flowsheet_runners():
    from idaes_fi.tests import demo_flowsheet

    runners = api.get_module_flowsheet_runners(demo_flowsheet)
    assert isinstance(runners, dict)
    for key, value in runners.items():
        assert isinstance(value, api._FlowsheetRunnerInterface)


@pytest.mark.unit
def test_load_module():
    from idaes_fi.tests import demo_flowsheet

    def module_eq(m1, m2):
        # module names may be fully qualified or not,
        # but filenames should match exactly
        f1, f2 = m1.__file__, m2.__file__
        print(f"Check if {f1} == {f2}")
        return f1 == f2

    assert module_eq(
        api.load_module(name="idaes_fi.tests.demo_flowsheet"), demo_flowsheet
    )
    assert module_eq(api.load_module(path=demo_flowsheet.__file__), demo_flowsheet)
    with pytest.raises(ImportError):
        api.load_module("idaes_fi.tests.non_existent_module")


@pytest.mark.unit
def test_run_flowsheet_bad(tmpdb):
    with pytest.raises(ValueError):
        api.run_flowsheet(module_name=None, path=None, dbpath=tmpdb)
    with pytest.raises(ValueError):
        api.run_flowsheet(module_name=None, path="non_existent_file.py", dbpath=tmpdb)
    with pytest.raises(KeyError):
        api.run_flowsheet(
            module_name="idaes_fi.tests.demo_flowsheet",
            path=None,
            flowsheet_name="non_existent_flowsheet",
            dbpath=tmpdb,
        )
    # there are multiple flowsheets..
    with pytest.raises(ValueError):
        api.run_flowsheet(module_name="idaes_fi.tests.demo_flowsheet", dbpath=tmpdb)
    return


@pytest.mark.component
def test_run_flowsheet_ok(tmpdb):
    model = api.run_flowsheet(
        module_name="idaes_fi.tests.demo_flowsheet",
        flowsheet_name=flowsheet_var,
        dbpath=tmpdb,
    )
    assert model is not None
