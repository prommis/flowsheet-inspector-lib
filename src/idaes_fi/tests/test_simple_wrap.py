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
Tests for simplified wrapper API.
"""

import pytest


# pacify linter by defining functions
# (will be overwritten by exec() below)
def fi_wrap_my_main_function(x, y, z=None):
    return None


def fi_wrap_build_flowsheet():
    return None


def fi_wrap_solve_flowsheet():
    return None


# redefine 2 functions that will be needed by original name
def build_flowsheet():
    return fi_wrap_build_flowsheet()


def solve_flowsheet():
    return fi_wrap_solve_flowsheet()
