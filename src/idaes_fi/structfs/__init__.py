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

import logging

__all__ = ["FlowsheetRunner", "Runner", "fi_main", "get_report_db"]

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

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def fi_main(*args, **kwargs):
    from .simple_wrap import _Wrapper

    return _Wrapper.main(*args, **kwargs)


def get_default_report_db():
    from .runner import Runner

    return Runner.get_default_report_db()
