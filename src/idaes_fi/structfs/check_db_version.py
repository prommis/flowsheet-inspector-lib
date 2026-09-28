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
Check the schema version of the flowsheet report database.

The ``fi-check-db-version`` command prints one line of JSON::

    {"is_db_version_low": true, "client_db_version": 1.0,
     "flowsheet_inspector_lib_db_version": 1.1}

It can also be run as ``python -m idaes_fi.structfs.check_db_version``.

``fi-steps`` and ``fi-run`` call :func:`refuse_if_db_outdated` before they
import a flowsheet. Importing a flowsheet opens the database and writes the
current version into it. After that an old schema looks like a current one.
To upgrade an old database, use ``fi-db-migration``.
"""

import argparse
import json
import logging
from pathlib import Path
import sqlite3
import sys
from typing import Any, Optional

from idaes.config import get_data_directory

from .reportdb import ReportDB

_log = logging.getLogger(__name__)

#: Schema version written by this library, as a major, minor tuple
LIB_VERSION = (ReportDB.MAJOR_VERSION, ReportDB.MINOR_VERSION)


def default_db_path() -> Path:
    """Path of the default report database. This is the file `Runner` uses."""
    data_dir, _, _ = get_data_directory()
    return Path(data_dir) / "reportdb.sqlite"


def db_path(db_file: Optional[str | Path]) -> Path:
    """`db_file` as a Path, or the default report database path if not given."""
    if db_file:
        return Path(db_file)
    return default_db_path()


def get_db_version(db_file: Optional[str | Path] = None) -> Optional[tuple[int, int]]:
    """Schema version stored in the database file, as a major, minor tuple.

    Returns None if there is no database yet, meaning no file or no tables.
    Returns 0, 0 for a database from before schema versioning. Those have
    no version table.

    Raises:
        sqlite3.Error: If the file cannot be read as a SQLite database.
    """
    path = db_path(db_file)
    if not path.exists():
        return None
    conn = sqlite3.connect(path)
    try:
        tables = []
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'"):
            tables.append(row[0])
        if ReportDB.VERSION_TABLE in tables:
            query = f"SELECT major, minor FROM {ReportDB.VERSION_TABLE}"
            row = conn.execute(query).fetchone()
            if row is None or row[0] is None or row[1] is None:
                return (0, 0)  # empty or broken version table, treat as pre-versioning
            return (int(row[0]), int(row[1]))
        if ReportDB.RPT_TABLE in tables:
            return (0, 0)  # reports table but no version table, so pre-versioning
        return None  # no report tables at all
    finally:
        conn.close()


def _number(version: Optional[tuple[int, int]]) -> float:
    """Turn a major, minor tuple into the number major.minor. No version gives 0.0."""
    if version is None:
        return 0.0
    return float(f"{version[0]}.{version[1]}")


def check_db_version(db_file: Optional[str | Path] = None) -> dict[str, Any]:
    """Compare the database file's schema version with this library's.

    Returns:
        A dict with three keys. ``is_db_version_low`` is True if the file's
        version is lower than the library's, so it must be migrated.
        ``client_db_version`` is the version in the file as the number
        major.minor, or 0.0 if there is none.
        ``flowsheet_inspector_lib_db_version`` is the version this library
        writes.
    """
    db_version = get_db_version(db_file)
    if db_version is None:
        is_low = False  # no database yet, it gets created on first use
    else:
        is_low = db_version < LIB_VERSION
    return {
        "is_db_version_low": is_low,
        "client_db_version": _number(db_version),
        "flowsheet_inspector_lib_db_version": _number(LIB_VERSION),
    }


def refuse_if_db_outdated(db_file: Optional[str | Path] = None) -> bool:
    """If the database version is too low, print the check JSON and log why.

    Returns:
        True if the caller must stop with exit code 3 instead of importing
        the flowsheet. False if the database is fine or cannot be checked.
    """
    try:
        result = check_db_version(db_file)
    except sqlite3.Error as err:
        _log.debug(f"Skipping report database version check: {err}")
        return False
    if not result["is_db_version_low"]:
        return False
    print(json.dumps(result))
    _log.error(
        f"Report database version is outdated: local database '{db_path(db_file)}' "
        f"is version {result['client_db_version']}, this version of idaes-fi "
        f"requires {result['flowsheet_inspector_lib_db_version']}. Upgrade it with "
        f"the command 'fi-db-migration' or with 'python -m idaes_fi.structfs.db_migration', "
        f"or click 'Upgrade FI DB' in the Flowsheet Inspector."
    )
    return True


def main(args: Optional[list[str]] = None) -> int:
    """Entry point for ``fi-check-db-version``. Prints the check as one line of JSON."""
    p = argparse.ArgumentParser(description="Check the report database schema version")
    p.add_argument(
        "-d", "--db", metavar="PATH", help="Database file, default is the default DB"
    )
    opts = p.parse_args(args)
    try:
        result = check_db_version(opts.db)
    except sqlite3.Error as err:
        print(
            f"ERROR: cannot read report database '{db_path(opts.db)}': {err}",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
