"""
Test ReportDB migration.
"""

import logging

import pytest

from idaes_fi.reportdb import ReportDB
from idaes_fi.reportdb_migrate import MigrationStrategy, MigrationError


@pytest.fixture(scope="module")
def setup_logging():
    from idaes_fi.reportdb_migrate import _log

    print("Setting up logging")
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    _log.addHandler(h)
    _log.setLevel(logging.DEBUG)
    return _log


@pytest.mark.unit
def test_migration_strategy_smoke():
    strategy = MigrationStrategy()


@pytest.mark.unit
def test_migration_strategy_migrate_invalid_file(tmp_path):
    strategy = MigrationStrategy()
    invalid_file = tmp_path / "invalid.db"
    with open(invalid_file, "w") as f:
        f.write("This is not a valid database file.")
    with pytest.raises(MigrationError):
        strategy.migrate(invalid_file)


# list old versions in order
old_versions = []
for mj in range(1, ReportDB.MAJOR_VERSION + 1):  # starts at 1
    for mn in range(0, ReportDB.MINOR_VERSION + 1):  # starts at 0
        # add all versions except current to list
        if not (mj == ReportDB.MAJOR_VERSION and mn == ReportDB.MINOR_VERSION):
            old_versions.append((mj, mn))


@pytest.mark.component
@pytest.mark.parametrize("from_ver", old_versions)
def test_migration_strategy_migrate(tmp_path, setup_logging, from_ver):
    from_maj, from_min = from_ver
    assert from_maj == 1  # only 1 major version
    assert from_min < ReportDB.MINOR_VERSION

    print(
        f"migrate ({from_maj}, {from_min}) -> ({ReportDB.MAJOR_VERSION}, {ReportDB.MINOR_VERSION})"
    )
    # Create a dummy 1.0 database file
    report_db_file = tmp_path / "report_db.sqlite"
    report_db_file.open("w").close()
    report_db = ReportDB(report_db_file)
    report_db.create()

    # simulate the old version (from_ver)
    # 1) version-specific logic
    if from_min < 1:
        # drop status table
        with report_db._connect() as conn:
            conn.execute(f"DROP TABLE IF EXISTS {report_db.STAT_TABLE}")
    if from_min < 2:
        # old report format (minimal)
        report_db.add_report({"actions": {"model_reports": "blabla"}, "last_run": 0})
    else:
        # new report format
        report_db.add_report({"actions": {"UnitModelReport": "blabla"}, "last_run": 0})

    # 2) modify version number
    with report_db._connect() as conn:
        conn.execute(
            f"UPDATE {report_db.VERSION_TABLE} SET major = {from_maj}, minor = {from_min}"
        )

    # Perform migration
    strategy = MigrationStrategy()
    did_something = False
    try:
        did_something = strategy.migrate(report_db_file)
    except MigrationError as e:
        pytest.fail(f"Migration failed: {e}")
    assert did_something, "Migration should have been performed, but wasn't"

    # Verify that status table exists now (1.1)
    with report_db._connect() as conn:
        rows = list(conn.execute("SELECT * from status"))
    # if we migrated from an older version, one status table
    # entry was created automatically (for the fake report item)
    if from_maj == 1 and from_min < 1:
        assert len(rows) == 1

    # Verify that report keys have correct names (1.2)
    rpt_data = report_db.get_last_report()
    assert list(rpt_data["actions"].keys()) == ["UnitModelReport"]
