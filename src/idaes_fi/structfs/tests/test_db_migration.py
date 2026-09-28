"""
Tests for the `fi-check-db-version` / `fi-db-migration` commands
(`idaes_fi.structfs.check_db_version`, `idaes_fi.structfs.db_migration`).
"""

import json
from pathlib import Path
import sqlite3

import pytest

from .. import check_db_version as cdv
from .. import db_migration as dbm
from ..reportdb import ReportDB

CODE = ReportDB.MAJOR_VERSION, ReportDB.MINOR_VERSION
CODE_NUM = float(f"{CODE[0]}.{CODE[1]}")
DEMO = "idaes_fi.structfs.tests.demo_flowsheet_structured"


def _last_json_line(out: str) -> dict:
    """Parse the last non-empty stdout line as JSON. This is how the UI reads it."""
    return json.loads([ln for ln in out.splitlines() if ln.strip()][-1])


def _set_version(dbfile, major=None, minor=None):
    db = ReportDB(str(dbfile))
    with db._connect() as conn:
        if major is not None:
            conn.execute(f"UPDATE {db.VERSION_TABLE} SET major = ?", (major,))
        if minor is not None:
            conn.execute(f"UPDATE {db.VERSION_TABLE} SET minor = ?", (minor,))


@pytest.fixture
def current_db(tmp_path):
    """A populated DB at the current schema version, 3 reports and 6 status rows."""
    dbfile = tmp_path / "current.sqlite"
    db = ReportDB(str(dbfile)).create()
    db.set_target(module="m", filedir="/d", filename="f.py", hash="h")
    for i in range(3):
        rid = db.add_report({"n": i}, name=f"run{i}", tags="x")
        db.add_status(rid, 1, "build", 1.0, 2.0, 0, "", None)
        db.add_status(rid, 2, "solve_initial", 3.0, 4.0, 0, "", True)
    return dbfile


@pytest.fixture
def old_db(current_db):
    """`current_db` with its stored major version set one behind the code."""
    _set_version(current_db, major=CODE[0] - 1)
    return current_db


@pytest.fixture
def legacy_db(tmp_path):
    """A DB from before schema versioning. It has no version table and old columns."""
    dbfile = tmp_path / "legacy.sqlite"
    with sqlite3.connect(str(dbfile)) as conn:
        conn.execute(
            "CREATE TABLE reports (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "created REAL, tags TEXT, solver_status TEXT, status BOOLEAN, "
            "report BLOB, name TEXT, module TEXT, filedir TEXT, filename TEXT, "
            "hash TEXT)"
        )
        conn.execute(
            "INSERT INTO reports (created, tags, solver_status, status, report, "
            "name, module, filedir, filename, hash) "
            "VALUES (1.0, 'a', 'ok', 1, ?, 'old', 'm', '/d', 'f.py', 'h')",
            (json.dumps({"legacy": True}).encode("utf-8"),),
        )
    return dbfile


# tests for the check


@pytest.mark.unit
def test_get_db_version(tmp_path, current_db, legacy_db):
    assert cdv.get_db_version(current_db) == CODE
    assert cdv.get_db_version(tmp_path / "nope.sqlite") is None
    empty = tmp_path / "empty.sqlite"
    sqlite3.connect(str(empty)).close()
    assert cdv.get_db_version(empty) is None
    assert cdv.get_db_version(legacy_db) == (0, 0)
    _set_version(current_db, major=CODE[0] + 1)
    assert cdv.get_db_version(current_db) == (CODE[0] + 1, CODE[1])  # not modified
    garbage = tmp_path / "garbage.sqlite"
    garbage.write_text("this is not a sqlite file, not even close")
    with pytest.raises(sqlite3.Error):
        cdv.get_db_version(garbage)
    # a broken version table counts as pre-versioning instead of crashing
    with sqlite3.connect(str(current_db)) as conn:
        conn.execute(f"UPDATE {ReportDB.VERSION_TABLE} SET major = NULL")
    assert cdv.get_db_version(current_db) == (0, 0)
    with sqlite3.connect(str(current_db)) as conn:
        conn.execute(f"DELETE FROM {ReportDB.VERSION_TABLE}")
    assert cdv.get_db_version(current_db) == (0, 0)


@pytest.mark.unit
def test_check_db_version(tmp_path, old_db, legacy_db):
    d = cdv.check_db_version(old_db)
    assert d == {
        "is_db_version_low": True,
        "client_db_version": float(f"{CODE[0] - 1}.{CODE[1]}"),
        "flowsheet_inspector_lib_db_version": CODE_NUM,
    }
    # a legacy DB reads as 0.0 and is low
    d = cdv.check_db_version(legacy_db)
    assert d["is_db_version_low"] is True and d["client_db_version"] == 0.0
    # older minor is low too
    _set_version(old_db, major=CODE[0], minor=CODE[1] - 1)
    assert cdv.check_db_version(old_db)["is_db_version_low"] is True
    # current, missing and newer DBs are not low
    _set_version(old_db, minor=CODE[1])
    assert cdv.check_db_version(old_db)["is_db_version_low"] is False
    d = cdv.check_db_version(tmp_path / "nope.sqlite")
    assert d["is_db_version_low"] is False and d["client_db_version"] == 0.0
    _set_version(old_db, major=CODE[0] + 1)
    d = cdv.check_db_version(old_db)
    assert d["is_db_version_low"] is False
    assert d["client_db_version"] == float(f"{CODE[0] + 1}.{CODE[1]}")


@pytest.mark.unit
def test_default_db_path():
    from ..runner import Runner

    try:
        expected = Runner.get_default_report_db().filename
    except ValueError:
        pytest.skip("no default report database on this machine")
    assert cdv.default_db_path() == Path(expected)


@pytest.mark.unit
def test_refuse_if_db_outdated(tmp_path, current_db, legacy_db, capfd, caplog):
    for ok_db in (current_db, tmp_path / "nope.sqlite", tmp_path):
        assert cdv.refuse_if_db_outdated(ok_db) is False
        assert capfd.readouterr().out == "" and caplog.text == ""
    # an outdated DB prints the check JSON on stdout and logs both versions and the command
    assert cdv.refuse_if_db_outdated(legacy_db) is True
    assert _last_json_line(capfd.readouterr().out) == cdv.check_db_version(legacy_db)
    err = caplog.text
    assert "is version 0.0" in err and f"requires {CODE_NUM}" in err
    assert "fi-db-migration" in err and "Upgrade FI DB" in err


@pytest.mark.unit
def test_check_main(old_db, tmp_path, capfd):
    assert cdv.main(["--db", str(old_db)]) == 0
    out, err = capfd.readouterr()
    assert len(out.strip().splitlines()) == 1
    assert _last_json_line(out)["is_db_version_low"] is True
    assert cdv.main(["--db", str(tmp_path / "nope.sqlite")]) == 0
    assert _last_json_line(capfd.readouterr().out)["is_db_version_low"] is False
    # an unreadable path gives an error, a non zero exit and no JSON
    assert cdv.main(["--db", str(tmp_path)]) == 1
    out, err = capfd.readouterr()
    assert out == "" and "ERROR" in err


# tests for the migration


@pytest.mark.unit
def test_migrate_old_major(tmp_path, old_db):
    old_ver = (CODE[0] - 1, CODE[1])
    d = dbm.migrate_db(old_db)
    assert d["migrated"] is True and d["rows_migrated"] == 9
    assert d["is_db_version_low"] is True  # as it was before migrating
    assert d["backup_file"].startswith(str(old_db) + ".bak-v")
    # file at the same path is now current and usable
    db = ReportDB(str(old_db))
    assert db.version == CODE
    db.test_connection()
    assert cdv.check_db_version(old_db)["is_db_version_low"] is False
    # data intact, ids preserved so status.run_id still matches reports.id
    assert db.get_last_report(name="run2") == {"n": 2}
    with db._connect() as conn:
        ids = [r[0] for r in conn.execute(f"SELECT id FROM {db.RPT_TABLE} ORDER BY id")]
        assert ids == [1, 2, 3]
        runs = [
            r[0]
            for r in conn.execute(
                f"SELECT DISTINCT run_id FROM {db.STAT_TABLE} ORDER BY 1"
            )
        ]
        assert runs == [1, 2, 3]
        solve_ok = conn.execute(
            f"SELECT solve_ok FROM {db.STAT_TABLE} WHERE step_name = 'solve_initial'"
        ).fetchall()
        assert solve_ok == [(1,), (1,), (1,)]
    assert db.add_report({"n": 3}, name="run3") == 4  # ids continue after old ones
    # backup next to the original, still at the old version
    assert ReportDB(d["backup_file"]).version == old_ver
    assert not list(tmp_path.glob("*.migrating"))


@pytest.mark.unit
def test_migrate_legacy(tmp_path, legacy_db):
    """Pre-versioning DB: extra columns dropped, new columns NULL, no backup."""
    d = dbm.migrate_db(legacy_db, backup=False)
    assert d["migrated"] is True and d["rows_migrated"] == 1
    assert d["backup_file"] is None
    db = ReportDB(str(legacy_db))
    db.test_connection()
    assert db.get_last_report(name="old") == {"legacy": True}
    meta = db.get_last_meta(name="old")
    assert meta["run_status"] is None and "status" not in meta
    assert not list(tmp_path.glob("*.bak-*"))


@pytest.mark.unit
def test_migrate_noop_and_failure(tmp_path, current_db, monkeypatch):
    # a current, missing or newer DB is left alone and gets no backup
    for db_file in (current_db, tmp_path / "nope.sqlite"):
        d = dbm.migrate_db(db_file)
        assert d["migrated"] is False and d["rows_migrated"] == 0
        assert d["backup_file"] is None
    _set_version(current_db, major=CODE[0] + 1)
    assert dbm.migrate_db(current_db)["migrated"] is False
    assert ReportDB(str(current_db)).version == (CODE[0] + 1, CODE[1])
    assert not list(tmp_path.glob("*.bak-*"))
    # an older minor version is migrated like any lower version
    _set_version(current_db, major=CODE[0], minor=CODE[1] - 1)
    d = dbm.migrate_db(current_db, backup=False)
    assert d["migrated"] is True and d["rows_migrated"] == 9
    assert ReportDB(str(current_db)).version == CODE
    # a failure leaves the original untouched and no temp file
    _set_version(current_db, major=CODE[0] - 1)

    def boom(new_path, old_path):
        raise sqlite3.OperationalError("boom")

    monkeypatch.setattr(dbm, "_copy_rows", boom)
    assert dbm.migrate_db(current_db)["migrated"] is False
    assert ReportDB(str(current_db)).version == (CODE[0] - 1, CODE[1])
    assert not list(tmp_path.glob("*.migrating")) and not list(tmp_path.glob("*.bak-*"))


@pytest.mark.unit
def test_migrate_refused_while_another_process_writes(tmp_path, old_db, monkeypatch):
    """A pending write in another connection must make the migration fail, not lose data."""
    monkeypatch.setattr(dbm, "LOCK_TIMEOUT", 0.2)  # do not wait the full 5 s in tests
    writer = sqlite3.connect(str(old_db), timeout=0)
    writer.execute("BEGIN IMMEDIATE")
    writer.execute("INSERT INTO reports (name) VALUES ('pending')")
    try:
        d = dbm.migrate_db(old_db, backup=False)
    finally:
        writer.commit()
        writer.close()
    assert d["migrated"] is False
    assert cdv.get_db_version(old_db) == (CODE[0] - 1, CODE[1])  # untouched
    with sqlite3.connect(str(old_db)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 4
    assert not list(tmp_path.glob("*.migrating"))
    # and once the writer is done, the migration goes through with all rows
    d = dbm.migrate_db(old_db, backup=False)
    assert d["migrated"] is True and d["rows_migrated"] == 10


@pytest.mark.unit
def test_migrate_main(old_db, tmp_path, capfd):
    assert dbm.main(["--db", str(old_db), "--no-backup"]) == 0
    d = _last_json_line(capfd.readouterr().out)
    assert d["migrated"] is True and d["backup_file"] is None
    assert not list(tmp_path.glob("*.bak-*"))
    # running it again does nothing and still exits 0
    assert dbm.main(["--db", str(old_db)]) == 0
    assert _last_json_line(capfd.readouterr().out)["migrated"] is False
    # an unreadable path gives an error, exit 1 and no JSON
    assert dbm.main(["--db", str(tmp_path)]) == 1
    out, err = capfd.readouterr()
    assert out == "" and "ERROR" in err


# fi-steps and fi-run refuse an outdated database before importing anything


@pytest.mark.component
def test_fi_steps_refuses_old_db(old_db, monkeypatch, capfd, caplog):
    from .. import common

    monkeypatch.setattr(cdv, "default_db_path", lambda: old_db)
    assert common.main("--fs", DEMO) == 3
    assert _last_json_line(capfd.readouterr().out)["is_db_version_low"] is True
    assert "fi-db-migration" in caplog.text
    # database untouched, importing the flowsheet did not write a new version
    assert cdv.get_db_version(old_db) == (CODE[0] - 1, CODE[1])
    # after migration, steps are listed
    assert dbm.migrate_db(old_db, backup=False)["migrated"] is True
    assert common.main("--fs", DEMO) == 0
    assert _last_json_line(capfd.readouterr().out)[0] == "build"


@pytest.mark.component
def test_fi_run_refuses_old_db(old_db, monkeypatch, capfd):
    from .. import fsrunner

    assert fsrunner.main([DEMO, "--db", str(old_db), "--last", "build"]) == 3
    out, err = capfd.readouterr()
    assert _last_json_line(out)["is_db_version_low"] is True
    assert "fi-db-migration" in err  # fi-run configures its own stderr log handler
    assert cdv.get_db_version(old_db) == (CODE[0] - 1, CODE[1])
    with sqlite3.connect(str(old_db)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 3
    # neither --help nor a refused run may touch the default DB either
    monkeypatch.setattr(cdv, "default_db_path", lambda: old_db)
    with pytest.raises(SystemExit):
        fsrunner.main(["-h"])
    assert old_db.name in capfd.readouterr().out  # shown as the default
    assert fsrunner.main([DEMO, "--last", "build"]) == 3
    capfd.readouterr()
    assert cdv.get_db_version(old_db) == (CODE[0] - 1, CODE[1])
