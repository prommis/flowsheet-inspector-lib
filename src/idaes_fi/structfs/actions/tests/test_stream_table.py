"""
Tests for stream table action
"""

import pytest

from .. import stream_table as ST
from idaes_fi.structfs.fsrunner import BaseFlowsheetRunner, FlowsheetRunner


@pytest.mark.unit
def test_smoke():
    # should fail with no runner obj
    with pytest.raises(Exception):
        obj = ST.StreamTable(runner=None)
    # should fail with wrong runner obj
    with pytest.raises(Exception):
        obj = ST.StreamTable(runner="runner")
    # should succeed with correct runner obj
    obj = ST.StreamTable(runner=BaseFlowsheetRunner())


@pytest.mark.unit
def test_report_empty():
    obj = ST.StreamTable(runner=BaseFlowsheetRunner())
    report = obj.report()
    assert report.index == []
    assert report.units == []
    assert report.columns == []
    assert report.data == []


@pytest.mark.unit
def test_report_none_data():
    # set up a stream table with some None values in the data
    obj = ST.StreamTable(runner=BaseFlowsheetRunner())
    obj._stream_table = {
        "columns": ["stream1", "stream2", "stream3"],
        "index": ["var1", "var2"],
        "units": ["unit1", "unit2"],
        # different variations of None in data
        "data": [
            ["unit", (1.0, "fixed"), (2.0, "free"), ("-", None)],
            ["unit", (1.0, "fixed"), (None, "free"), (3.0, None)],
        ],
    }

    # will fail if we don't first convert data
    with pytest.raises(ValueError):
        report = obj.report()

    # should succeed after converting data
    print(f"@@raw data: {obj._stream_table['data']}")
    obj._stream_table["data"] = obj._convert_data(obj._stream_table["data"])
    print(f"@@converted data: {obj._stream_table['data']}")
    report = obj.report()


@pytest.mark.component
def test_full_stream_names():
    """Test that stream names are fully qualified in the report."""
    from idaes_fi.structfs.tests.demo_flowsheet import build_flowsheet
    from pyomo.network import Arc

    # create a flowsheet
    runner = BaseFlowsheetRunner()
    runner._context.model = build_flowsheet()

    # generate stream table report
    obj = ST.StreamTable(runner=runner)
    obj.after_run()
    report = obj.report()

    # check that stream names are present in correct form (i.e. fully qualified)
    for component in runner.model.component_objects(Arc, descend_into=True):
        assert component.name in report.columns
