################################################################################
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
Tests for structfs __init__.py
"""

import pytest

from idaes_fi import structfs


@pytest.mark.unit
def test_exports():
    assert structfs.FlowsheetRunner
    assert structfs.Runner
    with pytest.raises(AttributeError):
        structfs.foo

    assert structfs.fi_main

    structfs.get_default_report_db()
