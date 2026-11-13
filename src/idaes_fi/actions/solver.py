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
"""Solver-related runner actions."""

from datetime import datetime
from io import StringIO
import sys

from pydantic import BaseModel
from pyomo.opt import check_optimal_termination
from pyomo.opt.results.container import ScalarData

from ..compute_diagnostics import (
    ComponentList,
    DiagnosticsData,
    DiagnosticsError,
    NumericalIssuesData,
    StructuralIssuesData,
)
from ..action_base import Action
from idaes_fi import FlowsheetRunner, Steps
from idaes_fi.common import is_solve_step


class SolverActionBase(Action):
    """Base class for actions to get solver state, output, etc."""

    def __init__(self, runner: FlowsheetRunner, **kwargs):
        """Initialize solver output capture state.

        Args:
            runner: Runner that owns this action.
            **kwargs: Additional keyword arguments passed to `Action`.
        """
        super().__init__(runner, **kwargs)

    def is_solve_step(self, name: str) -> bool:
        return is_solve_step(name)


class CaptureSolverOutput(SolverActionBase):
    """Capture the solver output."""

    class Report(BaseModel):
        """Report object for captured solver output action"""

        #: String of output keyed by step
        output: dict[str, str] = {}

    def __init__(self, runner, **kwargs):
        """Constructor

        Args:
            runner: FlowsheetRunner object
            kwargs: Arguments passed through to superclass
        """
        super().__init__(runner, **kwargs)

    def before_run(self):
        self._logs = {}
        self._solver_out = None
        self._save_stdout = None

    def before_step(self, step_name: str):
        """Action performed before the step."""
        if self.is_solve_step(step_name):
            self._solver_out = StringIO()
            sys.stdout.flush()
            self._save_stdout = sys.stdout
            sys.stdout = self._solver_out

    def after_step(self, step_name: str):
        """Action performed after the step."""
        self._restore_stdout(step_name)

    def _restore_stdout(self, step_name: str):
        if self._solver_out is not None:
            sys.stdout.flush()
            sys.stdout = self._save_stdout
            captured_out = self._solver_out.getvalue()
            self._logs[step_name] = captured_out
            self._solver_out = None
            # Clear the saved stdout too, so a later non-solve step that fails
            # does not see a stale `_save_stdout` and try to flush the
            # already-None `_solver_out` (which would raise and abort the run).
            self._save_stdout = None

    def step_failed(self, step_name: str, err: Exception):
        """Restore stdout and print the error when a step fails.

        Args:
            step_name: Name of the step that failed.
            err: The exception raised by the step.
        """
        self._restore_stdout(step_name)
        print(f"Solver error in step '{step_name}': {err}")

    def report(self) -> Report:
        """Machine-readable report with solver output.

        Returns:
            CaptureSolverOutput.Report
        """
        return self.Report(output=self._logs)


class SolverResult(BaseModel):
    """One solver result in `GetSolverResults.Report.result`"""

    problem: dict[str, int | float | str] = {}
    solver: dict[str, int | float | str] = {}
    values: dict[str, int | float | str | dict] = {}
    optimal: bool | None = None


class GetSolverResults(SolverActionBase):
    """Retrieve and structure the results from the solver."""

    class Report(BaseModel):
        """Report object for action"""

        #: Result(s) from Pyomo solver Result object,
        #: keyed by step, with each item being:
        #  - a list, for each time a solve was performed in the step, of:
        #     - a list of solve results for that solve
        results: dict[str, list[list[SolverResult]]] = {}

    def __init__(self, runner: FlowsheetRunner, **kwargs):
        """Constructor.

        Args:
            runner: Runner that owns this action.
            **kwargs: Additional keyword arguments passed to `Action`.
        """
        super().__init__(runner, **kwargs)
        self._results = {}

    def before_step(self, step_name: str) -> None:
        self._runner.solve_result = None
        self._runner.optimal = None

    def after_step(self, step_name: str):
        """Action performed after the step."""
        if self._runner.solve_result:
            result_list_set = []
            for item in self._runner.solve_result:
                if item is not None:
                    result_list = self._extract_results(item)
                    result_list_set.append(result_list)
            self._results[step_name] = result_list_set

    @staticmethod
    def _sval(v):
        # convert to a numeric or string value
        if isinstance(v, datetime):
            return v.timestamp()
        elif isinstance(v, float) or isinstance(v, int):
            return v
        return str(v)

    def _extract_results(self, r):
        # Solver quality is separate from process success: an infeasible ipopt
        # run returns normally, so only this flag records that the solve
        # "failed". check_optimal_termination needs a real Pyomo SolverResults;
        # anything else (empty dict before any solve, test doubles) is
        # "unknown" rather than an error.
        try:
            optimal = bool(check_optimal_termination(r))
            # propagate up to runner, so other actions can access this
            self._runner.optimal = optimal
        except (AttributeError, KeyError, TypeError):
            optimal = None

        # extract Pyomo dict of lists into a list of SolverResult objs
        # eg {"Solver": [{...}, ], "Problem": [{...},]} ->
        #    [SolverResult, SolverResult]
        # Add ScalarData items (single values) to every object
        result_list, scalars = [], {}
        for k, v in r.items():

            # Special processing for single-values
            if isinstance(v, ScalarData):
                vv = v.get_value()
                if isinstance(vv, dict):
                    scalar_value = {}
                    for k2, v2 in vv.items():
                        scalar_value[k2] = self._sval(v2)
                else:
                    scalar_value = self._sval(vv)
                scalars[k] = scalar_value
                continue  # done

            n = len(v)
            # make sure result list has space
            while n > len(result_list):
                result_obj = SolverResult(optimal=optimal)
                result_list.append(result_obj)
            # choose which part of result this is
            if k in ("Solver", "Problem"):
                sr_attr = k.lower()
            else:
                self.log.info(f"Ignoring unknown key in solver results: {k}")
                continue
            # extract Pyomo list for a given attr into SolverResult
            for i in range(n):
                v_dict = {}
                # convert values in dict to int, str, float, or None
                for v_k, v_v in v[i].items():
                    if hasattr(v_v, "get_value"):
                        v_v = v_v.get_value()
                    if isinstance(v_v, int) or isinstance(v_v, float):
                        v_dict[v_k] = v_v
                    else:
                        s = str(v_v)
                        if s == "<undefined>":
                            pass  # who cares? skip it
                        else:
                            v_dict[v_k] = s
                # set the corresponding i-th result attribute
                setattr(result_list[i], sr_attr, v_dict)

        # Add collected scalar values to every result in list
        for r in result_list:
            for k, v in scalars.items():
                r.values[k] = v

        return result_list

    def report(self) -> Report:
        """Report solver result.

        Returns:
            GetSolverResult.Report
        """
        return self.Report(results=self._results)


class Diagnostics(SolverActionBase):
    """Action to get model diagnostics."""

    class Report(BaseModel):
        """Report containing model diagnostics.

        These attributes should match keys of dict returned by the method
        `idaes_fi.compute_diagnostics.DiagnosticsData.all_as_obj()`.
        """

        #: This is False if there was no model to diagnose
        valid: bool = False
        #: If valid is True, all these should have values,
        #: otherwise they will all be None/null
        variables: ComponentList | None = None
        constraints: ComponentList | None = None
        structural_issues: StructuralIssuesData | None = None
        numerical_issues: NumericalIssuesData | None = None

    def __init__(self, runner, root, **kwargs):
        super().__init__(runner, **kwargs)
        if root is None or len(root) == 0:
            self._model_root_split = []
        else:
            self._model_root_split = root.split(".")
        self._had_solve = False
        self.diagnostics = {}

    def after_step(self, name):
        if self.is_solve_step(name):
            self._had_solve = True

    def after_run(self):
        """Get model diagnostics after the run."""
        m = self._runner.model
        if m is not None:
            # get submodel specified by root
            for a in self._model_root_split:
                m = getattr(m, a)
            try:
                dd = DiagnosticsData(model=m)
                if self._had_solve:
                    # get everything if a solve
                    self.diagnostics = dd.all_as_obj()
                else:
                    # TODO: get structural issues?
                    self.diagnostics = {}
            except DiagnosticsError as err:
                self.log.error(f"Diagnostics will be empty due to error: {err}")
                self.diagnostics = {}
            except TypeError as err:
                self.log.warning(f"Diagnostics error due to model object type: {err}")
                self.diagnostics = {}

    def report(self) -> Report:
        """Report containing model diagnostics information.

        Returns:
            Report object
        """
        report = self.Report()
        for key, val in self.diagnostics.items():
            setattr(report, key, val)
        report.valid = bool(self.diagnostics)
        return report
