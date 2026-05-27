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
Tests for reportdb module
"""

import pytest
from idaes_fi.structfs import reportdb


@pytest.fixture
def tmp_db_path(tmp_path):
    return tmp_path / "reportdb_test.db"


@pytest.fixture
def tmpdb(tmp_db_path):
    return reportdb.ReportDB(tmp_db_path)


@pytest.mark.unit
def test_db_version(tmpdb):
    # initialize database
    db = tmpdb
    db.create(exist_ok=False)
    # sanity-check that initial DB is ok
    db.test_connection()

    # add a fake report, which will be checked later
    report_data = {"Arthur Dent": "human", "Ford Prefect": "Betelgeusian"}
    db.add_report(report_data, name="db_test")

    # change minor version in DB
    new_ver = db.MINOR_VERSION + 1
    update_statement = f"UPDATE {db.VERSION_TABLE} SET minor = ?"
    with db._connect() as conn:
        conn.execute(update_statement, (new_ver,))
    # check that still ok
    db.test_connection()

    # change major version expect failure
    new_ver = db.MAJOR_VERSION + 1
    update_statement = f"UPDATE {db.VERSION_TABLE} SET major = ?"
    with db._connect() as conn:
        conn.execute(update_statement, (new_ver,))
    with pytest.raises(reportdb.DBError):
        db.test_connection()

    # recreate table and check again
    db.create(drop=False, exist_ok=True)
    # check that, once again, ok
    db.test_connection()
    # also make sure data is intact
    stored_report = db.get_last_report(name="db_test")
    assert stored_report == report_data


@pytest.mark.unit
def test_set_target(tmpdb):
    # empty is error
    with pytest.raises(ValueError):
        tmpdb.set_target(**{})
    # try each column
    all_col = {}
    for tgtcol in tmpdb.TARGET_COLUMNS:
        name = tgtcol[0]
        kw = {name: "value"}
        tmpdb.set_target(**kw)
        all_col.update(kw)
    # try all columns
    tmpdb.set_target(**all_col)
    # bad column
    with pytest.raises(KeyError):
        tmpdb.set_target(bad_column="value")


@pytest.mark.unit
def test_get_target(tmpdb):
    kw = {c[0]: "value" for c in tmpdb.TARGET_COLUMNS}
    tmpdb.set_target(**kw)
    # change values in input keywords
    for c in tmpdb.TARGET_COLUMNS:
        kw[c[0]] = "value1"
    # assure that value in tmpdb has not changed
    tgt = tmpdb.get_target()
    for c in tmpdb.TARGET_COLUMNS:
        assert kw[c[0]] != tgt[c[0]]
        # modify value returned by get_target
        tgt[c[0]] = kw[c[0]]
    # assure that changes to get_target return value
    # are not in the object (i.e. it is a copy)
    tgt = tmpdb.get_target()
    for c in tmpdb.TARGET_COLUMNS:
        assert kw[c[0]] != tgt[c[0]]


@pytest.mark.unit
def test_connect():
    bad_path = "/"
    db = reportdb.ReportDB(bad_path)
    with pytest.raises(reportdb.DBError):
        db.test_connection()


@pytest.mark.unit
def test_get_last_meta(tmpdb):
    tmpdb.create(exist_ok=False)
    # empty db returns  None
    assert tmpdb.get_last_meta() is None
    # add a fake record
    tags = "tag1 tag2"
    tmpdb.add_report({"name": "value"}, tags=tags)
    m = tmpdb.get_last_meta()
    assert m["tags"] == tags
