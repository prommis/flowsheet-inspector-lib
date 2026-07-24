"""Regression tests for the diagnostics evidence collector."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pyomo.opt import SolverResults, SolverStatus, TerminationCondition

COLLECTOR_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "collect_diagnostics.py"
)
SPEC = importlib.util.spec_from_file_location(
    "prommis_collect_diagnostics", COLLECTOR_PATH
)
assert SPEC is not None and SPEC.loader is not None
collector = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = collector
SPEC.loader.exec_module(collector)


class FakeRunner:
    def __init__(
        self,
        *,
        model: Any,
        results: Any = None,
        failed: bool = False,
        failed_actions: dict[str, str] | None = None,
    ) -> None:
        self.model = model
        self.results = results
        self.failed = failed
        self.failed_actions = failed_actions or {}
        self.run_requests: list[dict[str, str]] = []

    def get_defined_steps(self) -> list[str]:
        return ["build", "solve"]

    def run_steps(self, **kwargs: str) -> None:
        self.run_requests.append(kwargs)


class FakeToolbox:
    def __init__(self, model: Any) -> None:
        self.model = model
        self.structural_calls = 0
        self.numerical_calls = 0
        self.followup_calls = 0

    def report_structural_issues(self) -> None:
        self.structural_calls += 1
        print("Next Step: display_followup()")

    def report_numerical_issues(self) -> None:
        self.numerical_calls += 1
        print("Numerical report complete")

    def display_followup(self) -> None:
        self.followup_calls += 1
        print("Focused follow-up complete")


def _target_file(tmp_path: Path) -> Path:
    target = tmp_path / "wrapped_flowsheet.py"
    target.write_text("# imported through a test double\n", encoding="utf-8")
    return target


def _optimal_results() -> SolverResults:
    results = SolverResults()
    results.solver.status = SolverStatus.ok
    results.solver.termination_condition = TerminationCondition.optimal
    results.solver.message = "test solve complete"
    return results


def _patch_collection(
    monkeypatch: pytest.MonkeyPatch,
    runner: FakeRunner,
    toolbox: FakeToolbox | None = None,
) -> None:
    module = SimpleNamespace(FS=runner)
    monkeypatch.setattr(collector, "_import_target", lambda _path: module)
    monkeypatch.setattr(
        collector,
        "_runtime_record",
        lambda: {"python_executable": sys.executable, "packages": {}},
    )
    if toolbox is not None:
        import idaes.core.util

        monkeypatch.setattr(
            idaes.core.util,
            "DiagnosticsToolbox",
            lambda _model: toolbox,
        )


@pytest.mark.unit
def test_capture_records_timing_output_and_exception() -> None:
    def fail() -> None:
        print("before failure")
        raise ValueError("intentional")

    phase, value = collector._capture("example", fail)

    assert value is None
    assert phase["status"] == "error"
    assert phase["stdout"] == "before failure\n"
    assert phase["exception"]["type"] == "ValueError"
    assert phase["elapsed_seconds"] >= 0


@pytest.mark.unit
def test_missing_target_returns_timed_report(tmp_path: Path) -> None:
    arguments = collector._parser().parse_args([str(tmp_path / "missing.py")])

    report = collector.collect(arguments)

    assert report["outcome"] == "target_not_found"
    assert report["phases"] == []
    assert report["elapsed_seconds"] >= 0


@pytest.mark.unit
def test_default_collection_is_minimal_and_runs_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = FakeRunner(model=object(), results=_optimal_results())
    toolbox = FakeToolbox(runner.model)
    _patch_collection(monkeypatch, runner, toolbox)
    arguments = collector._parser().parse_args([str(_target_file(tmp_path))])

    report = collector.collect(arguments)

    phase_names = [phase["name"] for phase in report["phases"]]
    assert report["outcome"] == "collected"
    assert runner.run_requests == [{}]
    assert report["solver_probe"] is None
    assert "default_solver_probe" not in phase_names
    assert "diagnostics_method_discovery" not in phase_names
    assert "available_methods" not in report["diagnostics"]
    assert phase_names.count("runner_execution") == 1
    assert phase_names.count("diagnostics_structural") == 1
    assert phase_names.count("diagnostics_numerical") == 1
    assert toolbox.structural_calls == 1
    assert toolbox.numerical_calls == 1
    assert toolbox.followup_calls == 0
    assert report["diagnostics"]["suggested_methods"] == ["display_followup"]
    assert report["diagnostics"]["follow_up"]["status"] == "not_requested"
    assert report["solver_result"]["check_optimal_termination"] is True
    assert all(phase["elapsed_seconds"] >= 0 for phase in report["phases"])
    assert report["elapsed_seconds"] >= 0


@pytest.mark.unit
def test_explicit_report_suggested_follow_up_runs_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = FakeRunner(model=object(), results=_optimal_results())
    toolbox = FakeToolbox(runner.model)
    _patch_collection(monkeypatch, runner, toolbox)
    arguments = collector._parser().parse_args(
        [
            str(_target_file(tmp_path)),
            "--follow-up",
            "display_followup",
        ]
    )

    report = collector.collect(arguments)

    assert toolbox.followup_calls == 1
    assert report["diagnostics"]["follow_up"]["status"] == "ok"
    assert report["diagnostics"]["follow_up"]["method"] == "display_followup"
    assert "Focused follow-up complete" in report["diagnostics"]["follow_up"]["stdout"]
    assert [phase["name"] for phase in report["phases"]].count(
        "diagnostics_follow_up"
    ) == 1


@pytest.mark.unit
def test_unreported_follow_up_is_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = FakeRunner(model=object(), results=_optimal_results())
    toolbox = FakeToolbox(runner.model)
    _patch_collection(monkeypatch, runner, toolbox)
    arguments = collector._parser().parse_args(
        [str(_target_file(tmp_path)), "--follow-up", "not_in_report"]
    )

    report = collector.collect(arguments)

    assert toolbox.followup_calls == 0
    assert report["diagnostics"]["follow_up"]["status"] == "not_suggested"


@pytest.mark.unit
def test_runner_reported_failure_is_not_lost(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = FakeRunner(
        model=object(),
        failed=True,
        failed_actions={"initialize": "intentional failure"},
    )
    toolbox = FakeToolbox(runner.model)
    _patch_collection(monkeypatch, runner, toolbox)
    arguments = collector._parser().parse_args(
        [str(_target_file(tmp_path)), "--numerical", "no"]
    )

    report = collector.collect(arguments)

    run_phase = next(
        phase for phase in report["phases"] if phase["name"] == "runner_execution"
    )
    assert runner.run_requests == [{}]
    assert run_phase["status"] == "ok"
    assert report["outcome"] == "run_failed_with_evidence"
    assert report["runner"]["reported_failed"] is True
    assert report["runner"]["failed_actions"] == {"initialize": "intentional failure"}
    assert toolbox.structural_calls == 1
    assert toolbox.numerical_calls == 0


@pytest.mark.unit
def test_solver_probe_is_opt_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = FakeRunner(model=None)
    _patch_collection(monkeypatch, runner)
    calls = []

    def probe() -> dict[str, Any]:
        calls.append(True)
        return {"available": True, "version": [1, 2, 3]}

    monkeypatch.setattr(collector, "_default_solver_probe", probe)
    arguments = collector._parser().parse_args(
        [str(_target_file(tmp_path)), "--skip-run", "--probe-solver"]
    )

    report = collector.collect(arguments)

    assert calls == [True]
    assert runner.run_requests == []
    assert report["solver_probe"] == {"available": True, "version": [1, 2, 3]}
    assert [phase["name"] for phase in report["phases"]].count(
        "default_solver_probe"
    ) == 1


@pytest.mark.unit
def test_quiet_main_writes_json_without_stdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "report.json"
    monkeypatch.setattr(
        collector,
        "collect",
        lambda _arguments: {"outcome": "collected", "elapsed_seconds": 0.0},
    )

    exit_code = collector.main(["unused.py", "--output", str(output), "--quiet"])

    assert exit_code == 0
    assert capsys.readouterr().out == ""
    assert json.loads(output.read_text(encoding="utf-8"))["outcome"] == "collected"


@pytest.mark.integration
def test_real_runner_ipopt_and_diagnostics_integration(tmp_path: Path) -> None:
    pytest.importorskip("idaes_fi.structfs.fsrunner")
    from idaes.core.solvers import get_solver

    solver = get_solver()
    if not solver.available(exception_flag=False):
        pytest.skip("The installed default solver is unavailable")

    target = tmp_path / "tiny_wrapped_flowsheet.py"
    target.write_text(
        "from pyomo.environ import ConcreteModel, Constraint, Var\n"
        "from idaes.core import FlowsheetBlock\n"
        "from idaes.core.solvers import get_solver\n"
        "from idaes_fi.structfs.fsrunner import Context, FlowsheetRunner\n\n"
        "FS = FlowsheetRunner(steps=('build', 'set_solver', 'solve'))\n\n"
        "@FS.step('build')\n"
        "def build(context: Context):\n"
        "    model = ConcreteModel()\n"
        "    model.fs = FlowsheetBlock(dynamic=False)\n"
        "    model.fs.x = Var(initialize=1)\n"
        "    model.fs.y = Var(initialize=1)\n"
        "    model.fs.balance = Constraint(expr=model.fs.x + model.fs.y == 2)\n"
        "    model.fs.split = Constraint(expr=model.fs.x - model.fs.y == 0)\n"
        "    context.model = model\n\n"
        "@FS.step('set_solver')\n"
        "def set_solver(context: Context):\n"
        "    context.solver = get_solver()\n\n"
        "@FS.step('solve')\n"
        "def solve(context: Context):\n"
        "    context['results'] = context.solver.solve(context.model)\n",
        encoding="utf-8",
    )
    arguments = collector._parser().parse_args([str(target)])

    report = collector.collect(arguments)

    phase_names = [phase["name"] for phase in report["phases"]]
    assert report["outcome"] == "collected"
    assert phase_names.count("runner_execution") == 1
    assert report["runner"]["reported_failed"] is False
    assert report["solver_result"]["termination_condition"] == "optimal"
    assert report["solver_result"]["check_optimal_termination"] is True
    assert report["diagnostics"]["structural"]["status"] == "ok"
    assert report["diagnostics"]["numerical"]["status"] == "ok"
    assert all(phase["elapsed_seconds"] >= 0 for phase in report["phases"])
