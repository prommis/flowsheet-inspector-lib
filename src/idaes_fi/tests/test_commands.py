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
Tests for the idaes_fi commands (.commands) module
"""

from idaes_fi import commands
from .shared import flowsheet_var
import sys
from tempfile import NamedTemporaryFile

import pytest

__author__ = "Dan Gunter (LBNL)"


def run_command(args):
    sys.argv = args
    return commands.main()


@pytest.mark.unit
@pytest.mark.parametrize(
    "command",
    [
        "ifi",
        "ifi db",
        "ifi flowsheet",
        "ifi db info",
        "ifi db migrate",
        "ifi flowsheet run",
        "ifi flowsheet steps",
    ],
)
def test_command_basic(command):
    args = command.split(" ")
    with pytest.raises(SystemExit):
        run_command(args + ["--help"])
    run_command(args)


@pytest.mark.component
@pytest.mark.parametrize(
    "log_level",
    [
        "",
        "info",
        "debug",
        "warning",
    ],
)
def test_command_flowsheet_run(log_level):
    log_args = ["--level", log_level] if log_level else []
    for ok, demo_args in (
        (False, ["--name", "foo"]),
        (True, ["--name", flowsheet_var]),
    ):
        cmd_args = (
            ["ifi", "flowsheet"]
            + log_args
            + ["run", "--no-db", "--module", "idaes_fi.tests.demo_flowsheet"]
            + demo_args
        )
        print("Command: ", " ".join(cmd_args))
        result = run_command(cmd_args)
        if ok:
            assert result == 0
        else:
            assert result != 0

    for bad_args in (
        ["--module", "b.a.d.m.o.d.u.l.e"],
        ["--file", "/b/a/d/f/i/l/e.py"],
    ):
        result = run_command(["ifi", "flowsheet", "run"] + bad_args)
        assert result != 0
