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
Main API for using IDAES-PSE flowsheets with the Flowsheet Inspector.
"""

# stdlib
from abc import ABC, abstractmethod
import inspect
import importlib
from importlib.util import module_from_spec, spec_from_file_location
import logging
from pathlib import Path
import traceback
from types import ModuleType
from typing import Callable, Optional

# ext
from pydantic import BaseModel

# pkg
from .reportdb import ReportDB, init_report_db
from .action_base import Action
from .common import Steps

__author__ = "Dan Gunter (LBNL)"


class _LastStep(Exception):
    """Special exception for stopping the run after a given step."""

    pass


class _FlowsheetRunnerInterface(ABC):
    def __init__(self, steps: list[str] = None):
        self._model = None
        if steps is None:
            raise ValueError("Argument for steps must be a list of strings")
        try:
            self._steps = list(steps)
        except (ValueError, TypeError) as e:
            raise ValueError("Argument for steps must be a list of strings")
        self._steps = steps
        self._main = None
        self._last_step = None
        self._finalize = None
        self._results = []
        self._report = None
        self._actions = []
        self._optimal = None

    @abstractmethod
    def add_action(self, clazz, *args) -> bool:
        """Add a new action class plus optional args.

        Return:
            True if this was a new action, False if it replaced an existing action
            of the same class.
        """
        return False

    @abstractmethod
    def run_flowsheet(self, *args, **kwargs) -> object:
        pass

    @abstractmethod
    def step_begin(self, name: str):
        pass

    @abstractmethod
    def step_end(self):
        pass

    @abstractmethod
    def _get_main(self) -> Optional[Callable]:
        pass

    @abstractmethod
    def _set_main(self, fn: Optional[Callable]):
        pass

    main = property(_get_main, _set_main)

    @abstractmethod
    def _get_report_db_file(self) -> Path:
        pass

    report_db_file = property(_get_report_db_file, None)

    @abstractmethod
    def _get_model(self) -> object:
        pass

    @abstractmethod
    def _set_model(self, m: object):
        pass

    model = property(_get_model, _set_model)

    @abstractmethod
    def _get_steps(self) -> list[str]:
        pass

    steps = property(_get_steps, None)

    def _get_last_step(self) -> str:
        return self._last_step

    def _set_last_step(self, value: str):
        self._last_step = value

    last_step = property(_get_last_step, _set_last_step)

    def _get_results(self) -> object:
        return self._results

    def _set_results(self, value):
        if not value:
            self._results = []  # reset
        else:
            self._results.append(value)

    solve_result = property(_get_results, _set_results)

    def _get_report(self) -> dict[str, dict]:
        return self._report

    def _set_report(self, value: dict[str, dict]):
        self._report = value

    report = property(_get_report, _set_report)

    def _get_optimal(self) -> bool | None:
        return self._optimal

    def _set_optimal(self, value: bool | None):
        self._optimal = value

    optimal = property(_get_optimal, _set_optimal)

    def _get_report_db(self) -> ReportDB | None:
        return self._report_db

    report_db = property(_get_report_db, None)

    def report_db_off(self):
        self._report_db = None


class FlowsheetRunner(_FlowsheetRunnerInterface):
    """For using your flowsheet with the Flowsheet Inspector."""

    def __init__(
        self,
        steps: list[str],
        flowsheet_block: str = "fs",
        report_db: Optional[bool | str | Path | ReportDB] = True,
        quiet: bool = False,
    ):
        """Constructor.

        Args:
            steps: List of names of the steps in the flowsheet.
            flowsheet_block: Name in model of flowsheet block
            report_db: If True or None, get default DB. If False, do not
                       use a report db. Otherwise, use value as the report
                       database (must be a filename or ReportDB instance).
            quiet: If True, do not print anything to the console (logging
                   may still occur, but that is controlled separately)
        """
        super().__init__(steps=steps)
        self._quiet = quiet
        if report_db is False:
            self._report_db = None
        elif report_db is True or report_db is None:
            self._report_db = init_report_db()
        elif isinstance(report_db, ReportDB):
            self._report_db = report_db
        elif isinstance(report_db, Path) or isinstance(report_db, str):
            filename = Path(report_db)
            if not filename.exists():
                filename.open("w")  # create it
            self._report_db = ReportDB(filename)
            if filename.stat().st_size == 0:
                self._report_db.create(exist_ok=False)
        else:
            raise TypeError(
                "report_db must be True/False/None, "
                "a filename, or a ReportDB instance"
            )
        self._fs_name = flowsheet_block
        self._added_actions = []

        caller = inspect.currentframe().f_back
        self._caller_file = caller.f_globals.get("__file__") if caller else None

        self._init_log()

    def _reset(self):
        """Reset the internal state of the flowsheet runner, so that
        repeated calls to .run_flowsheet() behave correctly.
        """
        if self._report_db:
            self._report_db.test_connection()
        self._report_id = None
        self._completed_steps = []
        self._flowsheet_ended = False
        self._current_step = None
        self._model = None
        # reset all default actions
        self._actions = self._default_actions()

    def _init_log(self):
        self._fslog = logging.getLogger(__name__)
        logging.basicConfig(
            format="[%(levelname)s] %(asctime)s %(module)s - %(message)s"
        )

    def _get_report_db_file(self) -> Path:
        if self._report_db is None:
            return None
        return Path(self._report_db.filename)

    def _set_report_db_file(self, f: Path | str | ReportDB):
        if isinstance(f, ReportDB):
            self._report_db = f
        else:
            self._report_db = ReportDB(filename=f)
            self._report_db.create(exist_ok=True)

    #: Get report database file path
    report_db_file = property(_get_report_db_file, _set_report_db_file)

    def _get_model(self) -> object:
        return self._model

    def _set_model(self, m: object):
        self._model = m

    #: Get/set the model
    model = property(_get_model, _set_model)

    def _get_steps(self) -> list[str]:
        return self._steps

    # Get/set the list of steps
    steps = property(_get_steps, None)

    def _get_main(self) -> Optional[Callable]:
        return self._main

    def _set_main(self, fn: Optional[Callable]):
        if fn is not None and not callable(fn):
            raise TypeError("main must be callable or None")
        self._main = fn

    # Get/set the main flowsheet function
    main = property(_get_main, _set_main)

    # Log level getter/setter
    @property
    def log_level(self):
        return self._fslog.getEffectiveLevel()

    @log_level.setter
    def log_level(self, level: int):
        self._fslog.setLevel(level)

    # End of properties

    def _default_actions(self) -> list[Action]:
        from .actions import (
            GitHash,
            MermaidDiagram,
            UnitModelReport,
            ModelVariables,
            GetSolverResults,
            StreamTable,
            CaptureSolverOutput,
            Diagnostics,
            Timer,
            UnitDofChecker,
            Progress,
        )

        # dof_steps = [Steps.build, Steps.solve_initial, Steps.solve_optimization]

        return [
            clazz(self, *args)
            for clazz, args in (
                (CaptureSolverOutput, ()),
                (Diagnostics, (self._fs_name,)),
                # (UnitDofChecker, (self._fs_name, dof_steps)),
                (MermaidDiagram, (self._fs_name,)),
                (UnitModelReport, ()),
                (ModelVariables, ()),
                (GetSolverResults, ()),
                (StreamTable, ()),
                (Timer, ()),
                (GitHash, (self._caller_file,)),
                (Progress, ()),
            )
        ] + [clazz(self, *args) for clazz, args in self._added_actions]

    def add_action(self, clazz, *args):
        new_action = True
        for i, (c, a) in enumerate(self._added_actions):
            if c is clazz:
                self._added_actions[i] = (clazz, args)
                new_action = False
                break
        if new_action:
            self._added_actions.append((clazz, args))
        return new_action

    def run_flowsheet(self, *args, **kwargs) -> object:
        """Run the flowsheet.

        Args:
           args: Positional arguments passed to `runner.main`.
           kwargs: Keyword arguments passed to `runner.main`.
        """
        if self._main is None:
            raise ValueError("Must set .main function before calling run_flowsheet")

        self._save_args = args
        self._save_kwargs = kwargs

        self._reset()  # reset internal state

        self._log("begin")

        # create a new (empty) report row
        if self._report_db:
            self._report_id = self._report_db.add_report({})
            # let all the actions know the new report id
            for action in self._actions:
                action.run_id = self._report_id

        # before-run actions
        for action in self._actions:
            action.before_run()

        try:
            run_error, result = None, None
            result = self._main(self, *args, **kwargs)
        except Exception as err:
            if isinstance(err, _LastStep):
                # special exception; not an error
                self._log("end (last step)")
            else:
                self._log("end", error=err)
                run_error = err
                self._failed_step = self._current_step
            self._current_step = None

        self._flowsheet_end(error=run_error)

        return result

    def step_begin(self, name: str):
        # close prev step, if needed
        if self._current_step is not None:
            self.step_end()

        # setup
        self._current_step, self._failed_step = name, None
        self._log("begin")

        # run actions
        for action in self._actions:
            action.before_step(self._current_step)

    def step_end(self):
        # checks
        if self.model is None:
            raise ValueError("Must call set_model before end of first step")
        if self._current_step is None:
            raise ValueError("step_end called without matching step_begin")

        # run actions
        for action in self._actions:
            action.after_step(self._current_step)

        # finalize
        self._log("end")
        self._completed_steps.append(self._current_step)

        self._fslog.debug(
            f"check step '{self._current_step}' == last step '{self._last_step}'"
        )
        if not self._flowsheet_ended and self._last_step == self._current_step:
            raise _LastStep(self._current_step)  # exit

        self._current_step = None

    def _step_failed(self, name, err):
        for action in self._actions:
            action.step_failed(name, err)

    def _flowsheet_end(self, error=None):
        # cleanup from error, if necessary
        if error:
            self._step_failed(self._failed_step, error)

        # close out last step, if needed
        if self._current_step is not None:
            self._flowsheet_ended = True
            self.step_end()

        # run actions
        for action in self._actions:
            action.after_run()

        report = self._create_report()
        if self._report_db is not None:
            self._save_report(report, error)
        elif not self._quiet:
            self._print_report(report, error)
        self._report = report

        self._log("end")

    def _log(self, stage: str, error=None):
        what = f"flowsheet.{self._current_step}" if self._current_step else "flowsheet"
        msg = f"{what}::{stage}"
        if error is not None:
            msg += f" error={error}"
        self._fslog.info(msg)

    def _create_report(self) -> dict[str, dict]:
        """Compile reports of each action into a combined report

        Returns:
            dict: Mapping with two key-value pairs:
                    - `actions`: Keys are names given to actions during `add_action()`, values are the
                      reports returned by that action, in Python dictionary form.
                    - `last_run`: List of steps (names, as strings) in previous run
        """
        # create a mapping of actions to report dicts
        action_reports = {}
        for action in self._actions:
            rpt = action.report()
            rpt_dict = rpt.model_dump() if isinstance(rpt, BaseModel) else rpt
            name = action.name
            action_reports[name] = rpt_dict
        # return actions and other metadata as a report
        return {"actions": action_reports, "last_run": self._completed_steps}

    def _save_report(self, report: dict, error: Optional[Exception] = None):
        if Steps.solve_optimization in self._completed_steps:
            solver_status = True
        else:
            solver_status = False

        if error:
            # build a full error message
            tb = error.__traceback__
            tb_text = "".join(traceback.format_tb(tb))
            error_msg = f"{error.__class__.__name__}: {error}\nTraceback:\n{tb_text}"
            run_status = False
        else:
            error_msg = ""
            run_status = True

        self._report_db.add_report(
            report,
            tags="",
            solver_status=solver_status,
            run_status=run_status,
            run_exc=error_msg,
            update_row_id=self._report_id,
        )

    def _print_report(self, report: dict, error: Optional[Exception] = None):
        if error:
            print(f"ERROR: {error}")
        actions = report["actions"]
        solver_out = actions["CaptureSolverOutput"]["output"]
        solver_results = actions["GetSolverResults"]["results"]

        def status_word(opt):
            if opt is None:
                return "unknown"
            return ("failed", "success")[opt]

        for name, output in solver_out.items():
            tstat = []
            if name in solver_results:
                r = solver_results[name]
                for solve in r:
                    status_list = [status_word(problem["optimal"]) for problem in solve]
                    tstat.append("/".join(status_list))
            tstat_str = " ; ".join(tstat) if tstat else "unknown"
            print(
                f"--- {name} ---\n"
                f"Termination: {tstat_str}\n"
                f"{output}\n--- End ({name}) ---"
            )
        # json.dump(report, sys.stdout, indent=2)


class NullFlowsheetRunner(_FlowsheetRunnerInterface):
    """Empty flowsheet runner that does nothing."""

    def __init__(self, *args, **kwargs):
        super().__init__([""])

    def add_action(self, clazz, *args) -> bool:
        return False

    def run_flowsheet(self, *args, **kwargs) -> object:
        if self._main:
            return self._main(self, *args, **kwargs)
        else:
            return None

    def step_begin(self, name: str):
        pass

    def step_end(self):
        pass

    def _get_main(self) -> Optional[Callable]:
        return self._main

    def _set_main(self, fn: Optional[Callable]):
        self._main = fn

    def _get_report_db_file(self) -> Path:
        return Path()

    def _get_model(self) -> object:
        return self._model

    def _set_model(self, m: object):
        self._model = m

    def _get_steps(self) -> list[str]:
        return self._steps

    report_db_file = property(_get_report_db_file, None)
    model = property(_get_model, _set_model)
    steps = property(_get_steps, None)
    main = property(_get_main, _set_main)


# ----
# Utility functions
# ----


def get_module_flowsheet_runners(m: ModuleType) -> dict[str, _FlowsheetRunnerInterface]:
    """Get list of variables in a module that are FlowsheetRunner-s."""
    result = {}
    for key in dir(m):
        v = getattr(m, key)
        if isinstance(v, _FlowsheetRunnerInterface):
            result[key] = v
    return result


def load_module(name: Optional[str] = None, path: Optional[Path] = None) -> ModuleType:
    """Load a Python module from the given name or file path.
    Exactly one of `name` or `path` must be provided.

    Args:
        name: Name of the module to load. (Optional)
        path: Path to the Python file to load as a module. (Optional)

    Returns:
        The loaded module.

    Raises:
        ImportError: If the module cannot be loaded from the given name or path.
    """
    if name:
        module = importlib.import_module(name)
    else:
        path = Path(path).resolve()
        name = path.stem
        spec = spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from {path}")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


def run_flowsheet(
    module_name: Optional[str] = None,
    path: Optional[Path] = None,
    flowsheet_name: Optional[str] = None,
    dbpath: Optional[Path | bool] = None,
):
    """Run specified flowsheet (or only one) in specified module.
    Exactly one of `name` or `path` must be provided.

    Args:
        module_name: Name of the module to load. (Optional)
        path: Path to the Python file to load as a module. (Optional)
        flowsheet_name: Name of the variable with the FlowsheetRunner object to run.
            Only needed if there are multiple FlowsheetRunner-s in the module. (Optional)
        dbpath: Path to the database file. If not given, use default location.
                If set to False, disable database usage. (Optional)

    Raises:
        ValueError: If no FlowsheetRunner-s are found in the module, or if multiple are found but no flowsheet_name is specified.
        KeyError: If the specified flowsheet_name does not exist in the module.
    """
    if module_name is None and path is None:
        raise ValueError("Either module_name or path must be specified")
    try:
        module = load_module(module_name, path)
    except FileNotFoundError as e:
        raise ValueError(f"Cannot load module from path '{path}'") from e
    except ImportError as e:
        raise ValueError(f"Cannot load module '{module_name}'") from e

    runners = get_module_flowsheet_runners(module)
    if len(runners) == 0:
        raise ValueError(f"No FlowsheetRunner-s found in module '{module.__name__}'")
    if len(runners) == 1:
        runner = list(runners.values())[0]
    elif flowsheet_name is None:
        raise ValueError(
            f"Multiple FlowsheetRunner-s found in module '{module.__name__}', "
            "but no flowsheet_name was specified"
        )
    else:
        runner = runners.get(flowsheet_name, None)
        if runner is None:
            raise KeyError(
                f"No flowsheet '{flowsheet_name}' in module '{module.__name__}'"
            )

    if dbpath is not None:
        runner.report_db_file = dbpath
    elif dbpath is False:
        runner.report_db_file = None

    try:
        result = runner.run_flowsheet()
    except Exception as e:
        raise
    return result
