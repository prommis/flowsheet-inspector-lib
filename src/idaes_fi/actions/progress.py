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
Action to report progress of a flowsheet run.

This will add to the output report, under the key associated
with the action ("progress"), a list of steps.

```
"steps": [
    {
        "name": <step-name>,
        "status": <running|completed|failed>,
        "start": <timestamp>,
        "dur": <duration in seconds>,
        "err": <error message if failed>,
        "tb": <traceback if failed>,
        "env": <environment variables if failed>
    },
]
```
"""

# stdlib
from enum import Enum
import os
import time
import traceback

# package
from ..action_base import Action
from idaes_fi.reportdb import ReportDB
from idaes_fi.common import is_solve_step

# third-party
from pydantic import BaseModel


class Status(str, Enum):
    """Status of a step in a flowsheet run."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StepInfo(BaseModel):
    """Information about a step in a flowsheet run."""

    name: str
    number: int
    status: Status
    start: float
    dur: float | None = None
    err: str | None = None
    tb: list[str] | None = None
    env: dict[str, str] | None = None
    solve_ok: bool | None = None


class Progress(Action):
    """Action to track the progress of a run."""

    class Report(BaseModel):
        """Report for the progress of a run."""

        steps: list[StepInfo]

    def __init__(self, runner, **kwargs):
        super().__init__(runner, **kwargs)
        self._report_db = runner.report_db
        if self._report_db is not None:
            self.run_id = self._report_db.get_last_run_id()
        else:
            self.log.warning("Progress action initialized without a report database.")

    def before_run(self):
        self._step_info = []

    def before_step(self, step_name: str):
        """Record progress before a step is run."""
        t = time.time()
        step_num = len(self._step_info) + 1
        info = StepInfo(name=step_name, number=step_num, status=Status.RUNNING, start=t)
        self._step_info.append(info)

    def after_step(self, step_name: str):
        """Record progress after a step is run."""
        t = time.time()
        info = self._step_info[-1]
        info.solve_ok = self._calculate_solve_ok(step_name)
        info.dur = t - info.start
        # add record to reportdb if available
        if self._report_db is not None:
            self._report_db.add_status(
                run_id=self.run_id,
                step_num=info.number,
                step_name=info.name,
                errcode=0,
                start=info.start,
                duration=info.dur,
                solve_ok=info.solve_ok,
            )

    def _calculate_solve_ok(self, step_name: str) -> bool | None:
        """Calculate whether solve was ok.

        Solve step? -> None (n/a)

        Otherwise:
         - check self._runner.optimal, set by the `GetSolverResults` action
         - if False, the solve was not optimal -> False
         - else, either it was optimal (True) or we can't tell -> True
        """
        if not is_solve_step(step_name):
            return None
        return not (self._runner.optimal is False)

    def step_failed(self, step_name: str, error: Exception):
        """Record progress after a step fails."""
        if len(self._step_info) == 0:
            self._get_logger().warning(
                f"Step '{step_name}' did not begin before it failed."
            )
            return  # do nothing
        t = time.time()
        info = self._step_info[-1]
        info.solve_ok = False if is_solve_step(step_name) else None
        info.dur = t - info.start
        info.err = str(error)
        info.tb = self._format_tb(error)
        info.env = os.environ.copy()
        # add record to reportdb if available
        if self._report_db is not None:
            self._report_db.add_status(
                run_id=self.run_id,
                step_num=info.number,
                step_name=info.name,
                errcode=1,
                start=info.start,
                duration=info.dur,
                solve_ok=info.solve_ok,
            )

    def _format_tb(self, e: Exception) -> list[str]:
        tb_list = traceback.format_tb(e.__traceback__)
        return tb_list

    def report(self) -> Report:
        return self.Report(steps=self._step_info)
