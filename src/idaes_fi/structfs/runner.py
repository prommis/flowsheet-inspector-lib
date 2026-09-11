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
Run functions in a module in a defined, named, sequence.
"""

import importlib
import logging
from pathlib import Path
import time
import traceback
from typing import Callable, Optional, Tuple, Sequence, TypeVar

# third party
from pydantic import BaseModel
import sqlite3

# package
from idaes.config import get_data_directory
from .action_base import Action
from .reportdb import ReportDB, DBError
from .common import ActionNames, Steps
from .. import gitutil

__author__ = "Dan Gunter (LBNL)"

_log = logging.getLogger(__name__)


class Step:
    """Step to run by the `Runner`."""

    SEP = "::"  # when printing out step::label

    def __init__(self, name: str, func: Callable):
        """Constructor

        Args:
            name: Name of the step
            func: Function to call to execute the step
        """
        self.name: str = name
        self.func: Callable = func
        self.labels: list[str] = []


# Python 3.9-compatible forward reference
ActionType = TypeVar("ActionType", bound="Action")  # pylint: disable=C0103


class Runner:
    """Run a set of defined steps."""

    STEP_ANY = "-"

    def __init__(self, steps: Sequence[str], report_db: ReportDB = None):
        """Constructor.

        Args:
            steps: List of step names, in the order they sho
            report_db: Report database to use (otherwise default one)
        """
        self._context = {}
        self._actions: dict[str, ActionType] = {}
        if steps:
            self._step_names = steps
            self._dynamic_steps = False
        else:
            self._step_names = []
            self._dynamic_steps = True
        self._steps: dict[str, Step] = {}
        self._failed = False
        self._actions_failed = {}
        self.reset()
        self._tags = ""  # for reporting
        self._report_db = report_db or self.get_default_report_db(create=True)

    @property
    def failed(self) -> bool:
        return bool(self._failed)

    @property
    def failed_actions(self) -> dict[str, str]:
        return self._actions_failed.copy()

    def get_defined_steps(self) -> list[str]:
        """Get list of defined step (names)."""
        return [name for name in self._step_names if self._steps.get(name, None)]

    def get_report_db(self) -> ReportDB:
        """Get current report database.

        Returns:
            ReportDB: Default report DB instance
        """
        return self._report_db

    def set_report_db(
        self,
        db: Optional[ReportDB] = None,
        dbfile: Optional[Path | str] = None,
        create: bool = True,
    ) -> ReportDB:
        """Set a new value for the report database.

        If the database in `dbfile` exists, the required tables
        will be added if they do not already exist.

        Args:
            db: New report database
            dbfile: Path to reportdb file.
            create: Create report database if it does not exist.

        Returns:
            ReportDB: Previous report database

        Raises:
            ValueError: If neither argument is provided
            DBError: If database is corrupt or cannot be created
        """
        if db is None:
            # Get ReportDB from path
            if dbfile is None:
                raise ValueError("Either a `db` or `dbfile` argument is required")
            # get a ReportDB instance, creating DB if necessary and allowed
            do_create = False
            dbfile = Path(dbfile)
            if not dbfile.exists() and not create:
                raise ValueError(
                    f"Database file `{dbfile}` does not exist and `create` flag is False"
                )
            try:
                db = ReportDB(dbfile).create(exist_ok=True)
            except sqlite3.Error as err:
                raise DBError(err)

        # first, test that DB is valid
        assert isinstance(db, ReportDB)
        db.test_connection()

        # then, swap out any previous value for new db
        prev, self._report_db = self._report_db, db

        # if there was a previous one, copy its metadata
        prev_tgt = prev.get_target()
        if prev_tgt:
            self._report_db.set_target(**prev_tgt)

        return prev

    @classmethod
    def get_default_report_db(cls, create=False) -> ReportDB:
        """Get the default report database.

        Args:
            create (bool, optional): If true, create it if not found. Defaults to False.

        Raises:
            ValueError: If create is False and the database is not found

        Returns:
            ReportDB: Default report DB instance
        """
        # get IDAES home directory
        data_dir, _, _ = get_data_directory()
        data_path = Path(data_dir)

        # set reportdb to be a file in that directory
        report_db_path = data_path / "reportdb.sqlite"

        # set `db` to a new ReportDB instance
        if not report_db_path.exists() and not create:
            raise ValueError(f"Report database not found at path: {report_db_path}")
        # create(exist_ok=True) is safe on an existing DB and adds any missing
        # tables (e.g. the `status` table) to a database created by an older
        # schema, so opening a pre-existing DB also migrates it forward.
        db = ReportDB(report_db_path)
        db.create(exist_ok=True)

        return db

    def test_db_connection(self):
        self._report_db.test_connection()

    def __getitem__(self, key):
        """Look for key in `context`"""
        return self._context[key]

    def __getattr__(self, key):
        """For attributes not in the class, look to see if they
        match attributes on the context and if so return that value.
        """
        if key and key[0] == "_":
            raise AttributeError(key)
        if hasattr(self._context, key):
            return getattr(self._context, key)
        raise AttributeError(
            f"Runner object has no attribute '{key}' and "
            f"'{key}' is not an attribute of the context object"
        )

    def add_step(self, name: str, func: Callable):
        """Add a step.

        Steps are executed by calling `func(context)`,
        where `context` is a dict (or dict-like) object
        that is used to pass state between steps.

        Args:
            name: Add a step to be executed
            func: Function to execute for the step.

        Raises:
            KeyError: If a duplicate step is added, or the step is
                      not in the list of known steps (if step order is not from source)
        """
        step_name = self.normalize_name(name)

        if self._dynamic_steps:
            if step_name in self._step_names:
                raise KeyError(f"Duplicate step: {step_name}")
            self._step_names.append(step_name)
        elif step_name not in self._step_names:
            steppenlist = ", ".join(self._step_names)
            raise KeyError(f"Unknown step: '{step_name}' not in: {steppenlist}")
        self._steps[step_name] = Step(step_name, func)

    def add_label(self, base_name, name):
        """Add a label for a given step.

        labels are all executed, in the order added,
        immediately after their base step is executed.

        Args:
            base_name: Step name
            name: Substep name

        Raises:
            KeyError: Base step or label is not found
            ValueError: Base step does not have any labels
        """
        label_name = self.normalize_name(name)
        base_step_name = self.normalize_name(base_name)
        if base_step_name not in self._step_names:
            raise KeyError(f"Unknown step {base_step_name} for label {label_name}")
        try:
            step = self._steps[base_step_name]
        except KeyError:
            raise ValueError(f"Empty step {base_step_name} for label {label_name}")
        step.labels.append(label_name)

    def run_step(self, name, **kwargs):
        """Syntactic sugar for calling `run_steps` for a single step."""
        self.run_steps(first=name, last=name, **kwargs)

    def run_steps(
        self,
        first: str = "",
        last: str = "",
        after: str = "",
        before: str = "",
        closest_step=False,
        save_report=True,
    ):
        """Run steps from `first`/`after` to step `last`/`before`.

           Specify only one of the first/after and last/before pairs.

           Use the special value `STEP_ANY` to mean the first or last defined step.

        Args:
            first: First step to run (include)
            after: Run first defined step after this one (exclude)
            last: Last step to run (include)
            before: Run last defined step before this one (exclude)
            closest_step: If True, and step given is empty, that's ok since we will run the closest step;
                          If False, require that the specified steps be non-empty (default)
            save_report: If true save report in report database, if False don't do this

        Raises:
            KeyError: Unknown or undefined step given
            ValueError: Steps out of order or both first/after or before/last given
        """
        if first and after:
            raise ValueError("Cannot specify both 'after' and 'first'")
        if last and before:
            raise ValueError("Cannot specify both 'before' and 'last'")
        if not self._steps:
            return  # nothing to do, no steps defined
        args = (
            first or after,
            last or before,
            (bool(first) or not bool(after), bool(last) or not bool(before)),
            closest_step,
        )
        self._save_report_flag = save_report
        if save_report:
            self._start_report_record()
        self._run_steps(*args)
        if save_report:
            try:
                self._save_report()
            except DBError as err:
                _log.error(str(err))

    def _run_steps(
        self, first: str, last: str, endpoints: tuple[bool, bool], closest: bool
    ):
        names = (self.normalize_name(first), self.normalize_name(last))

        # Try to complete the report target, from value of 'module'
        tgt = self.get_report_target()
        if "module" in tgt:
            tgt_changed = False
            try:
                modname = tgt["module"]
                if modname:
                    mod = importlib.import_module(modname)
                else:
                    mod = None
            except ImportError as err:
                _log.error(f"Cannot import module {modname}")
                mod = None
            if mod:
                p = None
                if mod.__name__ == "__main__":
                    # if in VSCode, use special attr
                    nb_path = getattr(mod, "__vsc_ipynb_file__", None)
                    if nb_path:
                        p = Path(nb_path)
                        # clear any existing values
                        tgt.update({"filename": "", "filedir": ""})
                else:
                    try:
                        p = Path(mod.__file__)
                    except AttributeError as err:
                        _log.warning(f"Cannot set file for module '{mod}': {err}")
                if p is not None:
                    if not tgt.get("filename", "") and not tgt.get("filedir", ""):
                        tgt["filename"] = p.name
                        tgt["filedir"] = str(p.parent.absolute())
                        tgt_changed = True
                    if not tgt.get("hash", ""):
                        repo_hash = gitutil.git_head_hash(p)
                        if repo_hash is not None:
                            tgt["hash"] = repo_hash
                            tgt_changed = True
            if tgt_changed:
                _log.debug(f"setting report target: {tgt}")
                self.set_report_target(**tgt)

        self._last_run_steps = []

        # get indexes of first/last step
        _log.info(
            f"get indexes of first step '{names[0]}' and last step '{names[1]}' "
            f"in steps {self._step_names}"
        )
        step_range = [-1, -1]
        for i, step_name in enumerate(names):
            if step_name == self.STEP_ANY:  # meaning first or last defined
                # this will always find a step as long as there is at least one,
                # which we checked before calling this function
                idx = self._find_step(reverse=i == 1)
            else:
                try:
                    idx = self._step_names.index(step_name)
                except ValueError:
                    raise KeyError(f"Unknown step: {step_name}")
                if step_name not in self._steps:
                    if closest:
                        _log.warning(
                            f"Step {step_name} is empty, will run closest step"
                        )
                    else:
                        raise KeyError(f"Empty step: {step_name}")
            step_range[i] = idx

        # check that first comes before last
        if step_range[0] > step_range[1]:
            raise ValueError(
                "Steps out of order: {names[0]}={step_range[0]} > {names[1]}={step_range[1]}"
            )

        # Start with success, my friend
        self._failed = False

        # execute overall before-run action
        for action_name, action in self._actions.items():
            try:
                action.before_run()
            except Exception as err:
                _log.error(
                    f"{action_name} failed in 'before_run' (no other actions will be run)"
                )
                where = action_name + ".after_run"
                self._failed = (where, err)
                self._actions_failed[where] = err
                break  # one failure => all failure

        # run each (defined) step (if before did not fail)
        if self._failed:
            _log.error("Failures occurred in actions before run, skipping all steps")
        else:
            for i in range(step_range[0], step_range[1] + 1):
                # check whether to skip endpoints in range
                if (i == step_range[0] and not endpoints[0]) or (
                    i == step_range[1] and not endpoints[1]
                ):
                    continue
                # get the step associated with the index
                step = self._steps.get(self._step_names[i], None)
                # if the step is defined, run it
                if step:
                    step_begin_t = time.time()
                    step.func(self._context)
                    step_end_t = time.time()
                    ok = not bool(self._failed)
                    errmsg = "" if ok else str(self._failed[1])
                    solve_ok = self._solve_status(step.name)
                    self._log_step(
                        i, step.name, step_begin_t, step_end_t, ok, errmsg, solve_ok
                    )
                if self._failed:
                    break  # stop

        # execute overall after-run action
        if self._failed:
            _log.error("Run failed")
        else:
            for action_name, action in self._actions.items():
                try:
                    action.after_run()
                except Exception as err:
                    _log.error(f"{action_name} failed in 'after_run'")
                    if self._failed:
                        _log.error("Multiple failures: only first will be reported")
                    else:
                        where = action_name + ".after_run"
                        self._failed = (where, err)
                        self._actions_failed[where] = err
                    continue  # allow all after_run actions, only record first failure

    def _solve_status(self, step_name: str) -> Optional[bool]:
        """Solver-quality status of a step, distinct from process success.

        A solve step where the solver finds no solution (e.g. ipopt reports
        infeasible) returns normally, so the process status alone would show
        it as successful. This asks the registered actions whether `step_name`
        is a solve step and, if so, whether the solve terminated optimally.

        The lookup is duck-typed (`is_solve_step` + `optimal_termination`)
        rather than an isinstance check against `GetSolverResults`, because
        importing that action here would be circular (actions import fsrunner,
        which imports this module).

        Args:
            step_name: Name of the step that just ran.

        Returns:
            True/False if a solver-results action classifies this as a solve
            step and knows the termination status; None if this is not a solve
            step, no such action is registered, or the status is unknown
            (e.g. the step raised before the solver stored results).
        """
        for action in self._actions.values():
            is_solve = getattr(action, "is_solve_step", None)
            optimal = getattr(action, "optimal_termination", None)
            if callable(is_solve) and callable(optimal) and is_solve(step_name):
                result = optimal()
                return None if result is None else bool(result)
        return None

    def _log_step(
        self,
        step_num: int,
        step_name: str,
        begin_t: float,
        end_t: float,
        ok: bool,
        errmsg: str,
        solve_ok: Optional[bool] = None,
    ):
        """Record the outcome of a single step in the report DB `status` table.

        Also tracks the step as run (on success) or logs the failure.

        Args:
            step_num: Index of the step in the canonical step order.
            step_name: Name of the step.
            begin_t: Step start time (Unix timestamp, seconds).
            end_t: Step end time (Unix timestamp, seconds).
            ok: Whether the step succeeded (no exception raised).
            errmsg: Error message if the step failed, else empty string.
            solve_ok: Solver-quality status from :meth:`_solve_status` —
                True/False for optimal/non-optimal termination of a solve
                step, None for non-solve steps or unknown.
        """
        if self._save_report_flag:
            self._report_db.add_status(
                run_id=self._rpt_id,
                step_num=step_num,
                step_name=step_name,
                start=begin_t,
                duration=(end_t - begin_t),
                errcode=0 if ok else 1,
                errmsg=errmsg,
                solve_ok=solve_ok,
            )
        if ok:
            self._last_run_steps.append(step_name)
        else:
            _log.error(f"Step failed: {self._failed[0]}")

    def _start_report_record(self):
        """Start a new report record, which will later be updated with data.
        This allows updates to the the 'status' table referring to this report, before
        the full report data is available.
        """
        _log.debug("Starting report record in DB")
        # create empty report, remember its id
        self._rpt_id = self._report_db.add_report({})
        _log.debug(f"Created report record id={self._rpt_id} in DB")

    def _save_report(self):
        rpt = self.report()
        _log.debug(f"Adding report id={self._rpt_id} to DB")

        # get solver result (even if we failed!)
        try:
            # try to extract from report
            actions = rpt["actions"]
            solver_results_list = actions[ActionNames.SOLVER_RESULTS]["results"]
            last_result = solver_results_list[-1]
            solver_result = last_result["solver"]["Status"]
        except KeyError:
            # if that doesn't work, just set to an empty string
            solver_result = ""

        # get run result
        if self._failed:
            run_result = False
            # get exception as string XXX: maybe get trace?
            e = self._failed[1]
            tb = e.__traceback__
            tb_text = "".join(traceback.format_tb(tb))
            run_error = f"{e.__class__.__name__}: {e}\nTraceback:\n{tb_text}"
        else:
            run_result = True
            run_error = ""

        self._report_db.add_report(
            rpt,
            tags=self._tags,
            solver_status=solver_result,
            run_status=run_result,
            run_exc=run_error,
            update_row_id=self._rpt_id,
        )

    def set_report_target(self, **target_kw):
        """Set target for report generation.

        See reportdb.TARGET_COLUMNS for possible keys, also allow 'tags'.
        """
        self._tags = target_kw.pop("tags", "")  # I'm gonna pop some tags..
        _log.debug(f"Set report target to: {target_kw}")
        self._report_db.set_target(**target_kw)

    def get_report_target(self) -> dict:
        return self._report_db.get_target()

    def reset(self):
        """Reset runner internal state, especially the context."""
        self._context = {}
        self._last_run_steps = []
        self._failed = False
        self._actions_failed = {}

    def list_steps(self, all_steps=False) -> list[str]:
        """Get list of [runnable] steps."""
        result = []
        for n in self._step_names:
            if all_steps or (n in self._steps):
                result.append(n)
        return result

    def add_action(self, name: str, action_class: type, *args, **kwargs) -> object:
        """Add a named action.

        Args:
            name: Arbitrary name for the action, used to get/remove it
            action_class: Subclass of Action to use
            args: Positional arguments passed to `action_class` constructor
            kwargs: Keyword arguments passed to `action_class` constructor
        """
        obj = action_class(self, *args, **kwargs)
        self._actions[name] = obj
        return obj

    def get_action(self, name: str) -> ActionType:
        """Get an action object.

        Args:
            name: Name of action (as provided to `add_action`)

        Returns:
            ActionType: Action object

        Raises:
            KeyError: If action name does not match any known action
        """
        return self._actions[name]

    def remove_action(self, name: str):
        """Remove an action object.

        Args:
            name: Name of action (as provided to `add_action`)

        Raises:
            KeyError: If action name does not match any known action
        """
        del self._actions[name]

    def _find_step(self, reverse=False):
        start_step, end_step, incr = (
            (0, len(self._step_names), 1),
            (len(self._step_names) - 1, -1, -1),
        )[reverse]
        for i in range(start_step, end_step, incr):
            if self._step_names[i] in self._steps:
                return i
        return -1

    @classmethod
    def normalize_name(cls, s: Optional[str]) -> str:
        """Normalize a step name.
        Args:
            s: Step name

        Returns:
            normalized name
        """
        return cls.STEP_ANY if not s else s.lower()

    def _run_action_hook(self, hook_name: str, *args: object) -> None:
        """Invoke a step-level hook on every registered action, containing failures.

        Actions observe the run; an exception raised by one action's step hook
        is logged and recorded in `failed_actions`, but it stops neither the
        steps nor the other actions (matching how `after_run` failures are
        handled). Without this, a single failing action would abort the run
        before any step status could be recorded.

        Args:
            hook_name: Name of the Action method to call
                       (e.g. "before_step", "after_step")
            args: Arguments passed to the hook method
        """
        for action_name, action in self._actions.items():
            try:
                getattr(action, hook_name)(*args)
            except Exception as err:  # pylint: disable=W0703
                where = f"{action_name}.{hook_name}"
                _log.error(f"{where} failed (run continues): {err}")
                self._actions_failed[where] = err

    def _step_begin(self, name: str):
        self._run_action_hook("before_step", name)

    def _label_begin(self, base: str, name: str):
        self._run_action_hook("before_label", base, name)

    def _step_end(self, name: str):
        self._run_action_hook("after_step", name)

    def _label_end(self, base: str, name: str):
        self._run_action_hook("after_label", base, name)

    def _step_failed(self, name: str, err: Exception):
        self._run_action_hook("step_failed", name, err)

    def step(self, name: str):
        """Decorator function for creating a new step.

        Args:
            name: Step name

        Returns:
            Decorator function.
        """

        def step_decorator(func):

            def wrapper(*args, **kwargs):
                self._step_begin(name)
                ok, run_err = True, None
                try:
                    result = func(*args, **kwargs)
                except Exception as err:
                    ok, result, run_err = False, None, err
                if ok:
                    self._step_end(name)
                else:
                    self._failed = (name, run_err)
                    self._step_failed(name, run_err)
                return result

            self.add_step(name, wrapper)

            return wrapper

        return step_decorator

    def label(self, base: str, name: str):
        """Decorator function for creating a new label.

        Substeps are not run directly, and must have an already
        existing base step as their parent.

        Args:
            base: Base step name
            name: Substep name

        Returns:
            Decorator function.
        """

        def step_decorator(func):

            def wrapper(*args, **kwargs):
                self._label_begin(base, name)
                return func(*args, **kwargs)
                self._label_end(base, name)

            self.add_label(base, name)

            return wrapper

        return step_decorator

    def report(self) -> dict[str, dict]:
        """Compile reports of each action into a combined report

        Returns:
            dict: Mapping with two key-value pairs:
                    - `actions`: Keys are names given to actions during `add_action()`, values are the
                      reports returned by that action, in Python dictionary form.
                    - `last_run`: List of steps (names, as strings) in previous run
        """
        # create a mapping of actions to report dicts
        action_reports = {}
        for name, action in self._actions.items():
            rpt = action.report()
            rpt_dict = rpt.model_dump() if isinstance(rpt, BaseModel) else rpt
            action_reports[name] = rpt_dict
        # return actions and other metadata as a report
        return {"actions": action_reports, "last_run": self._last_run_steps.copy()}
