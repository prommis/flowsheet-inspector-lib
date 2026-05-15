#################################################################################
# The Institute for the Design of Advanced Energy Systems Integrated Platform
# Framework (IDAES IP) was produced under the DOE Institute for the
# Design of Advanced Energy Systems (IDAES).
#
# Copyright (c) 2018-2026 by the software owners: The Regents of the
# University of California, through Lawrence Berkeley National Laboratory,
# National Technology & Engineering Solutions of Sandia, LLC, Carnegie Mellon
# University, West Virginia University Research Corporation, et al.
# All rights reserved.  Please see the files COPYRIGHT.md and LICENSE.md
# for full copyright and license information.
#################################################################################
"""
Base class for runner actions.
"""

from __future__ import annotations

# stdlib
from abc import ABC, abstractmethod
import logging
from typing import Optional, TYPE_CHECKING

# third party
from pydantic import BaseModel

if TYPE_CHECKING:
    from .runner import Runner


class Action(ABC):
    """The Action class implements a simple framework to run arbitrary
    functions before and/or after each step and/or run performed
    by the `Runner` class.
    """

    def __init__(self, runner: Runner, log: Optional[logging.Logger] = None):
        """Constructor

        Args:
            runner: Reference to the runner that will trigger this action.
            log: Logger to use when logging informational or error messages
        """
        self._runner = runner
        if log is None:
            log = self._get_logger()
        self.log = log
        self._dbg = self.log.isEnabledFor(logging.DEBUG)

    def _get_logger(self):
        name = f"{__name__}.{self.__class__.__name__}"
        action_log = logging.root.manager.loggerDict.get(name, None)
        if action_log is None:
            action_log = logging.getLogger(name)
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "[%(levelname)s] %(asctime)s Action %(name)s (%(funcName)s): %(message)s"
                )
            )
            action_log.addHandler(handler)
        return action_log

    def before_step(self, step_name: str):
        """Perform this action before the named step.

        Args:
            step_name: Name of the step
        """
        return

    def before_substep(self, step_name: str, substep_name: str):
        """Perform this action before the named sub-step.

        Args:
            step_name: Name of the step
            substep_name: Name of the sub-step
        """
        return

    def after_step(self, step_name: str):
        """Perform this action after the named step.

        Args:
            step_name: Name of the step
        """
        return

    def after_substep(self, step_name: str, substep_name: str):
        """Perform this action after the named sub-step.

        Args:
            step_name: Name of the step
            substep_name: Name of the sub-step
        """
        return

    def step_failed(self, step_name: str, err: Exception):
        """Called if the step had an exception

        Args:
            step_name: Name of the step
            err: Exception object
        """
        return

    def before_run(self):
        """Perform this action before a run starts."""
        return

    def after_run(self):
        """Perform this action after a run ends."""
        return

    @abstractmethod
    def report(self) -> BaseModel | dict:
        """Report the results of the action to the caller.

        Returns:
            Results as a Pydantic model or Python dict
        """
        return
