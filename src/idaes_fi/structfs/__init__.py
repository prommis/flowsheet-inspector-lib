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

import logging

__all__ = ["FlowsheetRunner", "Runner", "fi_main", "get_report_db", "Steps"]

_log = logging.getLogger(__name__)

# Lazy exports, to avoid warnings when importing fsrunner, etc.
# using e.g. `python -m`


def __getattr__(name):
    if name == "FlowsheetRunner":
        from .fsrunner import FlowsheetRunner

        return FlowsheetRunner

    if name == "Runner":
        from .runner import Runner

        return Runner

    if name == "Steps":
        from .common import Steps

        return Steps

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def fi_main(*args, **kwargs):
    from .simple_wrap import _Wrapper

    return _Wrapper.main(*args, **kwargs)


def get_default_report_db():
    from .runner import Runner

    return Runner.get_default_report_db()
