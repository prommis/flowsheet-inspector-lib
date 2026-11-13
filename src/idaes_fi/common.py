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
Common constants and functions
"""

import argparse
from enum import Enum
import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import os
import sys
import traceback

DEFAULT_SOLVER_NAME = "ipopt"

#: Special key used to embed a flowsheet runner instance in a result dict
RESULT_FLOWSHEET_KEY = "__fi"


class Steps:
    """Names of steps so that editor autocomplete, etc., will help
    to avoid typos.
    """

    build = "build"
    set_solver = "set_solver"
    initialize = "initialize"
    set_operating_conditions = "set_operating_conditions"
    set_scaling = "set_scaling"
    solve_initial = "solve_initial"
    set_autoscaling = "set_autoscaling"
    add_costing = "add_costing"
    initialize_costing = "initialize_costing"
    setup_optimization = "setup_optimization"
    solve_optimization = "solve_optimization"

    index = (
        build,
        set_solver,
        initialize,
        set_operating_conditions,
        set_scaling,
        solve_initial,
        set_autoscaling,
        add_costing,
        initialize_costing,
        setup_optimization,
        solve_optimization,
    )

    @classmethod
    def __len__(cls):
        return len(cls.index)


def is_solve_step(name: str) -> bool:
    """Whether step `name` is the solve step.

    This will return True for any step in the standard solve steps
    or any user-defined step that starts with "solve_".

    Args:
        name: step name

    Returns:
        True if it is the solve step, otherwise False
    """
    # standard solve steps
    if name in (Steps.solve_initial, Steps.solve_optimization):
        return True
    # user-defined steps can use a naming convention starting with "solve_"
    if name.startswith("solve_"):
        return True
    return False
