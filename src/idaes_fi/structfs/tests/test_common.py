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


# Test the list-steps functionality of common.main()

TEST_DIR = Path(__file__).parent


@pytest.mark.integration
@pytest.mark.parametrize(
    "args,ok",
    [
        # default steps
        ([], True),
        # one flowsheet
        (
            [
                "--fs",
                # cwd is source directory
                str(TEST_DIR / "demo_flowsheet_structured.py"),
            ],
            True,
        ),
        # one flowsheet (2)
        (
            [
                "--fs",
                # cwd is source directory
                "idaes_fi.structfs.tests.demo_flowsheet_structured",
            ],
            True,
        ),
        # multiple flowsheets
        (
            [
                "--fs",
                str(TEST_DIR / "demo_flowsheet_structured_multi.py"),
                "--attr",
                "FS",
            ],
            True,
        ),
        (
            [
                "--fs",
                "idaes_fi.structfs.tests.demo_flowsheet_structured_multi",
                "--attr",
                "FS",
            ],
            True,
        ),
        # multiple flowsheets, bad attr
        (
            [
                "--fs",
                "idaes_fi.structfs.tests.demo_flowsheet_structured_multi",
                "--attr",
                "NO",
            ],
            False,
        ),
        # multiple flowsheets, need attr
        (
            [
                "--fs",
                str(TEST_DIR / "demo_flowsheet_structured_multi.py"),
            ],
            False,
        ),
        # no flowsheet in module
        (
            [
                "--fs",
                str(TEST_DIR / "test_common.py"),
            ],
            False,
        ),
        # no flowsheet in module (2)
        (
            [
                "--fs",
                "idaes_fi.structfs.tests.test_common",
            ],
            False,
        ),
        # bad file
        (["--fs", "/B/A/D/F/I/L/E.xxx"], False),
        # error in file
        (["--fs", "%"], False),
        # not even a file
        (["--fs", "%.py"], False),
    ],
)
def test_run_main(args, ok, subtests, tmp_path):
    print(f"file={__file__}")
    for fmt in ("text", "json", ""):
        with subtests.test(fmt):
            if fmt:
                args = args + ["-t", fmt]
            for i, a in enumerate(args):
                if a == "%":
                    f = tmp_path / "bad.py"
                    f.open("w").write("print(1 / 0)\n")
                    args[i] = str(f)
            retcode = common.main(*args)
            if ok:
                assert retcode == 0
            else:
                assert retcode != 0
