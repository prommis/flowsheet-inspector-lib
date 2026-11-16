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
Database migration.
"""

# stdlib
import json
import logging
from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile
import time

# third-party
import sqlite3

# local
from idaes_fi.reportdb import ReportDB
from idaes_fi.api import FlowsheetRunner

__author__ = "Dan Gunter (LBNL)"

_log = logging.getLogger(__name__)


class MigrationError(Exception):
    """Exception raised when a migration fails."""

    pass


class MigrationStrategy:
    """Database migration strategy.

    Usage:
        strategy = MigrationStrategy()
        strategy.migrate(filename)  # migrate a specific database file
        strategy.migrate()  # migrate the default report database file
    """

    def __init__(self):
        self._maj, self._min = ReportDB.MAJOR_VERSION, ReportDB.MINOR_VERSION

    def migrate(self, filename: Path = None) -> bool:
        """Perform the migration.

        Args:
            filename (Path, optional): Path to the database file. If None,
                uses the default report database file.

        Returns:
            True if migration was performed, False if not.

        Raises:
            MigrationError: If the migration cannot be performed due to version
                incompatibility or other issues.
        """
        _log.info(f"Migrate database in {filename}")
        if filename is None:
            filename = FlowsheetRunner().report_db_file
            _log.info("Migrating default report file: {filename}")
        old_db = ReportDB(filename)
        try:
            old_maj, old_min = old_db.version
        except sqlite3.DatabaseError as e:
            raise MigrationError(f"Cannot read version from database {filename}: {e}")
        _log.debug(f"Database at '{filename}' has version {old_maj}.{old_min}")
        # check that versions allow for migration
        if old_maj < self._maj:
            raise MigrationError(
                f"Cannot migrate from version {old_maj}.{old_min} to "
                f"{self._maj}.{self._min}: major version change."
            )
        elif old_maj > self._maj or (old_maj == self._maj and old_min > self._min):
            raise MigrationError(
                f"Cannot migrate from version {old_maj}.{old_min} to "
                f"{self._maj}.{self._min}: version in current database is newer "
                f"than version in library (you may need to update the library)."
            )
        elif old_maj == self._maj and old_min == self._min:
            _log.info(f"Database at '{filename}' is current, no migration needed")
            return False  # No migration needed

        # check complete, perform database migration
        _log.debug(
            f"Performing database migration from {old_maj}.{old_min} -> {self._maj}.{self._min}"
        )
        assert old_maj == self._maj and old_min < self._min

        # create empty DB in temporary file, which
        # will be the target of the migration
        tmp = NamedTemporaryFile("w+")
        tmp.close()  # Windows can't open the same file twice(!!)
        tmp_db = ReportDB(tmp.name)
        tmp_db.create()

        # Dispatch to migration function for this (old, new) version pair
        migration_func = f"migrate_{old_maj}_{old_min}_to_{self._maj}_{self._min}"
        if not hasattr(self, migration_func):
            raise MigrationError(
                f"No migration function defined for version {old_maj}.{old_min} "
                f"to {self._maj}.{self._min}."
            )
        try:
            getattr(self, migration_func)(old_db, tmp.name)
        except Exception as e:
            raise MigrationError(
                f"Migration from version {old_maj}.{old_min} to "
                f"{self._maj}.{self._min} failed: {e}"
            )

        # Move the temporary file to the original database location
        backup_filename = self._backup(filename)
        _log.debug(f"Backup of original database created at {backup_filename}.")
        shutil.copy(tmp.name, filename)
        _log.info(f"Database at {filename} migrated to {self._maj}.{self._min}")
        # note: tmp db file will be removed automatically

        return True  # migration performed

    @staticmethod
    def _backup(filename: str) -> str:
        """Create a backup of the database file."""
        t = time.time()
        ms = int((t - int(t)) * 1000)
        ts = time.strftime("%Y%m%d%H%M%S") + str(ms).zfill(3)
        backup_filename = f"{filename}-{ts}.bak"
        shutil.copy(filename, backup_filename)
        return backup_filename

    # ---
    # Migration functions
    #  name should be migrate_<old_major>_<old_minor>_to_<new_major>_<new_minor>
    # ---

    @staticmethod
    def _populate_status_table(old_filename, new_filename):
        with sqlite3.connect(old_filename) as old_conn:
            with sqlite3.connect(new_filename) as new_conn:
                for row in old_conn.execute(f"SELECT id FROM {ReportDB.RPT_TABLE}"):
                    q9 = ", ".join(["?"] * 9)
                    new_conn.execute(
                        f"INSERT INTO {ReportDB.STAT_TABLE} VALUES ({q9})",
                        (
                            row[0],  # report id
                            0,  # run_id
                            1,  # step_num
                            0.0,  # start
                            0.0,  # end
                            0.0,  # duration
                            0,  # errcode
                            "",  # errmsg
                            True,  # solve_ok
                        ),
                    )

    _rename_actions_map = {
        "solver_output": "CaptureSolverOutput",
        "solver_results": "GetSolverResults",
        "diagnostics": "Diagnostics",
        "degrees_of_freedom": "UnitDofChecker",
        "mermaid_diagram": "MermaidDiagram",
        "model_reports": "UnitModelReport",
        "model_variables": "ModelVariables",
        "stream_table": "StreamTable",
        "timings": "Timer",
        "git_hash": "GitHash",
        "progress": "Progress",
    }

    @classmethod
    def _rename_report_keys(cls, table: str, row: tuple):
        if table == ReportDB.RPT_TABLE:
            i = 6
            report_bytes = row[i]
            # convert UTF-8 encoded JSON to dict
            report = json.loads(report_bytes.decode("utf-8"))
            if not report:
                return row
            actions = report["actions"]
            # rename action keys
            orig_keys = list(actions.keys())
            delete_keys = []
            for k in orig_keys:
                if k in cls._rename_actions_map:
                    k2 = cls._rename_actions_map[k]
                    actions[k2] = actions[k]
                    delete_keys.append(k)
            for k in delete_keys:
                del actions[k]
            # convert dict back to UTF-8 encoded JSON
            new_report_bytes = json.dumps(report).encode("utf-8")
            row = list(row)
            row[i] = new_report_bytes
        return row

    def migrate_1_0_to_1_1(self, old_db: ReportDB, new_filename: str):
        hdr = f"Migrate ({old_db.filename}) 1.0 -> ({new_filename}) 1.1"

        # Copy data in report table without modification
        _log.debug(f"{hdr}: copy report data")
        self._copy_rows(
            old_db.filename, new_filename, ReportDB.RPT_TABLE, transform_func=None
        )

        # Populate status table with one row for each report
        _log.debug(f"{hdr}: populate status table")
        self._populate_status_table(old_db.filename, new_filename)

    def migrate_1_0_to_1_2(self, old_db: ReportDB, new_filename: str):
        hdr = f"Migrate ({old_db.filename}) 1.0 -> ({new_filename}) 1.2"

        # Rename report keys
        _log.debug(f"{hdr}: copy report data")
        self._copy_rows(
            old_db.filename,
            new_filename,
            ReportDB.RPT_TABLE,
            transform_func=self._rename_report_keys,
        )

        # Populate status table with one row for each report
        _log.debug(f"{hdr}: populate status table")
        self._populate_status_table(old_db.filename, new_filename)

    def migrate_1_1_to_1_2(self, old_db: ReportDB, new_filename: str):
        hdr = f"Migrate ({old_db.filename}) 1.1 -> ({new_filename}) 1.2"

        # Rename report keys
        _log.debug(f"{hdr}: copy report data")
        self._copy_rows(
            old_db.filename,
            new_filename,
            ReportDB.RPT_TABLE,
            transform_func=self._rename_report_keys,
        )

    # ---
    # Helper functions
    # ---

    @classmethod
    def _copy_rows(
        cls, src_filename: str, tgt_filename: str, table_name: str, transform_func=None
    ):
        """Copy rows from old database to new database."""
        with sqlite3.connect(src_filename) as src_conn:
            with sqlite3.connect(tgt_filename) as tgt_conn:
                for row in src_conn.execute(f"SELECT * FROM {table_name}"):
                    n = len(row)
                    if transform_func is not None:
                        row = transform_func(table_name, row)
                    tgt_conn.execute(
                        f"INSERT INTO {table_name} VALUES ({','.join(['?'] * n)})", row
                    )
