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
Simple wrapper
"""

# stdlib
import inspect
import logging
from pathlib import Path
import os

# package
from .fsrunner import BaseFlowsheetRunner
from .common import RESULT_FLOWSHEET_KEY, ActionNames, Steps
from .logutil import init_fi

_log = logging.getLogger(__name__)


class SimpleFlowsheetRunner(BaseFlowsheetRunner):
    """Rewrite FlowsheetRunner constructor to:
    (a) consider the build step (also) a solve step, and
    (b) have an attribute `main_func` for the main function
    """

    def __init__(self, *args, **kwargs):
        """Constructor."""
        from .actions import (  # pylint: disable=C0415
            Timer,
            UnitDofChecker,
            CaptureSolverOutput,
            GetSolverResults,
            ModelVariables,
            MermaidDiagram,
            StreamTable,
            Diagnostics,
            UnitModelReport,
        )

        super().__init__(*args, **kwargs)
        self.main_func = None
        self.main_func_args = []
        self.main_func_kwargs = {}
        dof_steps = [Steps.build, Steps.solve_initial, Steps.solve_optimization]
        # note: put solver_output first so stdout is re-enabled after
        # solve steps for all other actions
        self.add_action(ActionNames.SOLVER_OUTPUT.value, CaptureSolverOutput)
        self.add_action(ActionNames.DIAGNOSTICS.value, Diagnostics)
        self.add_action(ActionNames.DOF.value, UnitDofChecker, "fs", dof_steps)
        self.add_action(ActionNames.MERMAID_DIAGRAM.value, MermaidDiagram)
        self.add_action(ActionNames.MODEL_REPORTS.value, UnitModelReport)
        self.add_action(ActionNames.MODEL_VARIABLES.value, ModelVariables)
        self.add_action(ActionNames.SOLVER_RESULTS.value, GetSolverResults)
        self.add_action(ActionNames.STREAM_TABLE.value, StreamTable)
        self.add_action(ActionNames.TIMINGS.value, Timer)


# Global flowsheet runner, will create as needed
_FS = SimpleFlowsheetRunner()

# Init logging
init_fi()


class _Wrapper:
    """Wrapper to create fi_main() decorator."""

    MAIN_STEP_NAME = "build"

    # add a build step that simply calls the provided main function
    # to build & solve the model.
    @_FS.step(MAIN_STEP_NAME)
    def _build(ctx):
        model, solve_result = _FS.main_func(*_FS.main_func_args, **_FS.main_func_kwargs)
        ctx.model = model
        ctx.results = solve_result

    @classmethod
    def main(cls, solve=True, **main_kw):
        """Decorator *factory* for function that returns the tuple (model, results)
        after building and solving a model, so that it provides
        information through the FlowsheetRunner API.
        """
        # Set `solve_steps` to control solver-result-dependent reports.
        if solve:
            _log.debug("@fi_main() function contains solve")
            solve_steps = [cls.MAIN_STEP_NAME]
        else:
            _log.debug("@fi_main() function does not contain a solve")
            solve_steps = []
        _FS.set_solve_steps(solve_steps)

        def fi_wrapper_factory(main_fn):
            # note: don't change 'fi_wrapper' name, since this
            # is used for auto-detection of the method in user's code

            def fi_wrapper(*args, **kwargs):
                if "module" not in main_kw:
                    main_kw["module"] = inspect.getmodule(main_fn).__name__
                if "filename" not in main_kw:
                    main_file = inspect.getfile(main_fn)
                    main_file_path = Path(main_file).absolute()
                    main_kw["filename"] = main_file_path.name
                    main_kw["filedir"] = str(main_file_path.parent)
                # allow user to pass in alternate database file to main()
                if "dbfile" in kwargs:
                    _FS.set_report_db(dbfile=kwargs.pop("dbfile"))
                _FS.main_func = main_fn
                _FS.main_func_args = args
                _FS.main_func_kwargs = kwargs
                _FS.set_report_target(**main_kw)
                # run the flowsheet
                _FS.run_steps()
                # stash object in result dict under 'special' key
                results = _FS.results
                results[RESULT_FLOWSHEET_KEY] = _FS
                return _FS.model, results

            return fi_wrapper

        return fi_wrapper_factory
