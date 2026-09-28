#!/usr/bin/env python3
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
"""
Migrate the flowsheet report database to the current schema version.

The ``fi-db-migration`` command runs the same check as ``fi-check-db-version``.
Only if the library version is higher than the database file's, it
migrates the file. A new database with the current schema is built in a
temporary file. Every row of the report tables is copied into it. Columns
are matched by name and row ids are kept. The old file is backed up next to
it, then the temporary file replaces the old one in a single atomic step.
It prints the check JSON plus ``migrated``, ``backup_file`` and
``rows_migrated`` as one line.

It can also be run as ``python -m idaes_fi.structfs.db_migration``.
"""

import argparse
import datetime
import json
import logging
import os
from pathlib import Path
import sqlite3
import sys
from typing import Any, Optional

from .check_db_version import check_db_version, db_path, get_db_version
from .reportdb import DBError, ReportDB

_log = logging.getLogger(__name__)

#: The report tables that get copied. A new table in the schema must be added here.
TABLES = (
    (ReportDB.RPT_TABLE, ReportDB.RPT_COL),
    (ReportDB.STAT_TABLE, ReportDB.STAT_COL),
)

#: Seconds to wait for another process that is writing to the old database
LOCK_TIMEOUT = 5.0


def _copy_rows(new_path: Path, old_path: Path) -> int:
    """Copy all rows of the report tables from `old_path` into `new_path`. Returns the row count."""
    total = 0
    conn = sqlite3.connect(new_path)
    try:
        conn.execute("ATTACH DATABASE ? AS old", (str(old_path),))
        for table, columns in TABLES:
            # columns of this table in the old database
            old_cols = []
            for row in conn.execute(f"PRAGMA old.table_info({table})"):
                old_cols.append(row[1])
            if not old_cols:
                continue  # table did not exist in the old schema
            # copy only the columns that exist in both schemas
            common_cols = []
            for name, _ in columns:
                if name in old_cols:
                    common_cols.append(name)
            cols = ", ".join(common_cols)
            cur = conn.execute(
                f"INSERT INTO main.{table} ({cols}) "
                f"SELECT {cols} FROM old.{table} ORDER BY rowid"
            )
            total += cur.rowcount
        conn.commit()
    finally:
        conn.close()
    return total


def _backup(path: Path, version: tuple[int, int]) -> Path:
    """Make a consistent copy of the database `path` next to it."""
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak-v{version[0]}.{version[1]}-{stamp}")
    src = sqlite3.connect(path)
    dst = sqlite3.connect(backup_path)
    try:
        src.backup(dst)
    except sqlite3.Error:
        dst.close()
        backup_path.unlink(missing_ok=True)  # do not leave a half written backup
        raise
    finally:
        dst.close()
        src.close()
    return backup_path


def migrate_db(
    db_file: Optional[str | Path] = None, backup: bool = True
) -> dict[str, Any]:
    """Migrate the database file if its version is lower than the library's.

    Returns:
        The :func:`check_db_version` dict from before migrating, plus
        ``migrated``, ``backup_file`` and ``rows_migrated``.
    """
    path = db_path(db_file).resolve()
    result = check_db_version(path)
    result.update({"migrated": False, "backup_file": None, "rows_migrated": 0})
    if not result["is_db_version_low"]:
        return result
    old_version = get_db_version(path)
    assert old_version is not None
    tmp_path = path.with_name(path.name + ".migrating")
    lock = None
    try:
        # Hold a write lock on the old database while copying, so that no
        # other process can write rows that would then be lost. If someone
        # is writing right now this waits a few seconds and then fails.
        lock = sqlite3.connect(path, timeout=LOCK_TIMEOUT)
        lock.execute("BEGIN IMMEDIATE")
        tmp_path.unlink(missing_ok=True)
        ReportDB(str(tmp_path)).create(exist_ok=False)
        rows = _copy_rows(tmp_path, path)
        if backup:
            result["backup_file"] = str(_backup(path, old_version))
        # release the lock right before the swap, Windows cannot replace an open file
        lock.rollback()
        lock.close()
        lock = None
        os.replace(
            tmp_path, path
        )  # atomic, if anything above fails the old file is untouched
    except (sqlite3.Error, DBError, OSError) as err:
        _log.error(f"Migration failed, database '{path}' unchanged: {err}")
        return result
    finally:
        if lock is not None:
            lock.close()
        tmp_path.unlink(missing_ok=True)
    result.update({"migrated": True, "rows_migrated": rows})
    _log.info(
        f"Migrated '{path}' from {old_version} to {ReportDB.MAJOR_VERSION}.{ReportDB.MINOR_VERSION}"
    )
    return result


def main(args: Optional[list[str]] = None) -> int:
    """Entry point for ``fi-db-migration``. Migrates if needed and prints the result as JSON.

    Exit code is 0 if the database is at the current version afterwards, else 1.
    """
    p = argparse.ArgumentParser(
        description="Migrate the report database to the current schema"
    )
    p.add_argument(
        "-d", "--db", metavar="PATH", help="Database file, default is the default DB"
    )
    p.add_argument(
        "--no-backup", action="store_true", help="Do not keep a copy of the old file"
    )
    opts = p.parse_args(args)
    try:
        result = migrate_db(opts.db, backup=not opts.no_backup)
    except sqlite3.Error as err:
        print(
            f"ERROR: cannot read report database '{db_path(opts.db)}': {err}",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result))
    if result["migrated"]:
        return 0
    if not result["is_db_version_low"]:
        return 0  # nothing to migrate
    return 1  # migration failed, the error was logged


if __name__ == "__main__":
    sys.exit(main())
