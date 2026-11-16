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

# stdlib
from pathlib import Path
import pprint
import sys
from types import SimpleNamespace

import pytest
from pytest import approx
from pyomo.environ import ConcreteModel, Var
from pyomo.environ import units as pyunits
from pyomo.opt import SolverResults, SolverStatus, TerminationCondition
from pyomo.opt.results.container import ScalarData

from idaes_fi import FlowsheetRunner, Steps
from ..actions import (
    MermaidDiagram,
    Timer,
    GitHash,
    UnitDofChecker,
    StreamTable,
    CaptureSolverOutput,
    GetSolverResults,
    UnitModelReport,
)
from ..gitutil import git_head_hash
from . import demo_flowsheet
from .shared import flowsheet_var


@pytest.fixture
def tmp_runner(tmp_path):
    runner = FlowsheetRunner(
        steps=demo_flowsheet._steps, report_db=tmp_path / "test_runner_actions.db"
    )
    runner.main = demo_flowsheet.main
    return runner


@pytest.mark.unit
def test_class_timer(tmp_runner):
    timer = Timer(tmp_runner)

    # fake run
    timer.before_run()
    for step in tmp_runner.steps:
        timer.before_step(step)
        timer.after_step(step)
    timer.after_run()
    report = timer.report()

    # check report
    for step in tmp_runner.steps:
        assert report.timings[step] >= 0
    assert report.run_time >= 0


@pytest.mark.unit
def test_git_hash_action(tmp_runner):
    file_path = Path(__file__)
    action = GitHash(tmp_runner, file_path)

    assert action.report().hash is None

    action.after_run()
    hsh = action.report().hash
    print(f"Got Git hash: {hsh}")
    assert hsh == git_head_hash(file_path)


@pytest.mark.unit
def get_test_hash_action_bad(tmp_runner, tmp_path):
    # no such path
    file_path = tmp_path / "foo"
    action = GitHash(tmp_runner, file_path)
    action.after_run()
    assert action.report().hash is None
    # path but no git
    action = GitHash(tmp_runner, tmp_path)
    action.after_run()
    assert action.report().hash is None


@pytest.mark.unit
def test_unit_dof_action_base(tmp_runner):
    rn = tmp_runner

    def check_step(name, data):
        print(f"check_step {name} data: {data}")
        assert "fs.F03" in data
        if name == Steps.build:
            assert data["fs.F03"] >= 0

    def check_run(step_dof, model_dof):
        assert model_dof >= 0

    rn.add_action(UnitDofChecker, "fs", [Steps.build], check_step, check_run)

    rn.run_flowsheet()

    pprint.pprint(rn.report["actions"].keys())
    pprint.pprint(rn.report["actions"]["UnitDofChecker"])


@pytest.mark.unit
def test_mermaid_report(tmp_runner):
    rn = tmp_runner
    rn.run_flowsheet()

    action = None
    for a in rn._actions:
        if isinstance(a, MermaidDiagram):
            action = a
            break
    assert action

    action.set_model_root("fs")
    report = action.report()
    if action.diagram is None:
        print("Connectivity not installed")
        assert report == {}
    else:
        print("Connectivity IS installed")
        assert report.diagram != {}


@pytest.mark.unit
def test_stream_table_action_create(tmp_runner):
    obj = StreamTable(tmp_runner)
    assert obj


@pytest.mark.unit
def test_stream_table_action_report(tmp_runner):
    tmp_runner.model = demo_flowsheet.build_flowsheet()
    action = StreamTable(tmp_runner)
    action.after_run()
    report = action.report()
    print(f"report: {report}")
    # perform some basic checks on the contents
    assert report
    assert report.index[0].startswith("flow_mol")
    assert report.units[0] == "mole / second"
    assert "fs.s01" in report.columns
    assert len(report.columns) == len(report.data[0])
    assert len(report.data) == len(report.index)
    v1 = report.data[0][0]
    assert len(v1) == 2
    assert v1[0] > 0
    assert v1[0] <= 1
    assert v1[1] == "unfixed"


@pytest.mark.unit
def test_capture_solver_output():
    action = CaptureSolverOutput(SimpleNamespace())
    solve_step = Steps.solve_initial
    message = "solver did something"
    original_stdout = sys.stdout

    action.before_run()
    try:
        action.before_step(solve_step)
        print(message)
        action.after_step(solve_step)
        stdout_was_restored = sys.stdout is original_stdout
    finally:
        sys.stdout = original_stdout

    assert stdout_was_restored
    assert action.report().output == {solve_step: f"{message}\n"}
