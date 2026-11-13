"""
Tests to run before/after all others
"""

import pytest

from idaes_fi.reportdb import get_report_db_path


class State:
    """State shared across setup/teardown of the test suite"""

    report_db_path = None
    report_db_stat: float = 0.0

    @classmethod
    def is_changed(cls) -> bool:
        pstat = cls.report_db_path.stat()
        return pstat.st_mtime != cls.report_db_stat.st_mtime

    @classmethod
    def diff(cls) -> str:
        pstat = cls.report_db_path.stat()
        return f"(mtime) {cls.report_db_stat.st_mtime} -> {pstat.st_mtime}"


@pytest.fixture(scope="session", autouse=True)
def suite_setup_teardown():
    setup()
    yield  # run test suite


@pytest.fixture(autouse=True)
def check_db(request):
    # do nothing
    yield  # run the test
    if State.report_db_path is not None:
        if State.is_changed():
            diff = State.diff()
            # reset so subsequent tests don't fail due to the same change
            State.report_db_stat = State.report_db_path.stat()
            pytest.fail(
                f"Report DB '{State.report_db_path}' was changed during test: {diff}"
            )


def setup():
    """Code here runs before all tests start"""
    try:
        p = get_report_db_path()
    except Exception as e:
        pytest.fail(f"Failed to get report DB path: {e}")
    if p.exists():
        State.report_db_path = p
        State.report_db_stat = p.stat()
