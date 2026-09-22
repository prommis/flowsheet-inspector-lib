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
    status: Status
    start: float
    dur: float | None = None
    err: str | None = None
    tb: list[str] | None = None
    env: dict[str, str] | None = None


class Progress(Action):
    """Action to track the progress of a run."""

    class Report(BaseModel):
        """Report for the progress of a run."""

        steps: list[StepInfo]

    def __init__(self, runner, **kwargs):
        super().__init__(runner, **kwargs)

    def before_run(self):
        self._steps = []

    def before_step(self, step_name: str):
        """Record progress before a step is run."""
        t = time.time()
        info = StepInfo(name=step_name, status=Status.RUNNING, start=t)
        self._steps.append(info)

    def after_step(self, step_name: str):
        """Record progress after a step is run."""
        t = time.time()
        info = self._steps[-1]
        info.status = Status.COMPLETED
        info.dur = t - info.start

    def step_failed(self, step_name: str, error: Exception):
        """Record progress after a step fails."""
        t = time.time()
        info = self._steps[-1]
        info.status = Status.FAILED
        info.dur = t - info.start
        info.err = str(error)
        info.tb = self._format_tb(error)
        info.env = os.environ.copy()

    def _format_tb(self, e: Exception) -> str:
        tb_list = traceback.format_tb(e.__traceback__)
        return tb_list

    def report(self) -> Report:
        return self.Report(steps=self._steps)
