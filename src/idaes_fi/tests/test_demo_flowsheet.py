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
Tests that utilize the demo_flowsheet_structured.py module in this
directory.
"""

# stdlib
from pathlib import Path

# third-party
import pytest

# package
from .demo_flowsheet import f1_runner


@pytest.mark.unit
def test_has_runner():
    assert f1_runner is not None
    assert f1_runner.steps


@pytest.mark.integration
def test_run(tmp_path):

    dbpath = tmp_path / "test_fs_run_steps.db"
    f1_runner.report_db_file = dbpath
    f1_runner.run_flowsheet()
