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


from pathlib import Path
import pytest
from idaes_fi.structfs import common

MARKER = 1


@pytest.mark.unit
def test_module_attrs():
    assert common.DEFAULT_SOLVER_NAME
    assert common.RESULT_FLOWSHEET_KEY


@pytest.mark.unit
def test_action_names():
    # test that all capitalized keys have string values
    names = common.ActionNames
    for key in dir(names):
        if not key.startswith("_") and key.upper() == key:
            value = getattr(names, key).value
            assert isinstance(value, str)


@pytest.mark.unit
def test_steps():
    steps = common.Steps()
    for attr in steps.index:
        value = getattr(steps, attr)
        assert value
        assert isinstance(value, str)


@pytest.mark.unit
def test_load_module():
    module_name = "idaes_fi.structfs.tests.test_common"
    module_path = Path(__file__)
    print(f"module name={module_name} path={module_path}")

    mod1 = common.load_module(module_name)
    mod2 = common.load_module(module_path)
    mod3 = common.load_module(str(module_path))

    # break up so we can tell where failed
    assert mod1.MARKER == mod2.MARKER
    assert mod2.MARKER == mod3.MARKER
