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
Tools for looking at and testing the 'report' DB
implemented by module `idaes_fi.reportdb`.
"""

import argparse
import dataclasses
from dataclasses import dataclass, field
import datetime
from io import IOBase
import logging
from pathlib import Path
import re
import sqlite3
import sys
import time

import pandas as pd

from idaes_fi.api import init_report_db
from idaes_fi.reportdb import ReportDB, DBError

_log = logging.getLogger(__name__)


class CommandError(Exception):
    """Raised when a `fi-db` subcommand fails; carries the command name."""

    def __init__(self, command: str, error: str):
        """Build the error message.

        Args:
            command: Name of the subcommand that failed (e.g. "info").
            error: Underlying error or message.
        """
        msg = f"in command '{command}': {error}"
        super().__init__(msg)


@dataclass
class Info:
    """Summary information about a report database, filled in by the `info` command."""

    file: Path = None
    major_version: int = 0
    minor_version: int = 0
    num: int = 0
    date_range: list[float] = (0, 0)


def _info_command(args):
    """Run the `info` subcommand: print summary information about the database.

    Args:
        args: Parsed command-line arguments (uses `args.db`).

    Raises:
        CommandError: If the database cannot be read.
    """
    dbfile = args.db
    if dbfile is None:
        db = init_report_db()
    else:
        db = ReportDB(dbfile)
    try:
        info = _info_fetch(db)
    except DBError as err:
        raise CommandError("info", err)
    _info_print(info)


def _info_fetch(db: ReportDB) -> "Info":
    """Query a report database for its version, record count and date range.

    Args:
        db: Report database to inspect.

    Returns:
        Info: Populated summary information.

    Raises:
        DBError: If the database cannot be queried.
    """
    _applog.info(f"query database '{db.filename}'")
    info = Info()
    info.major_version, info.minor_version = db.version
    info.file = Path(db.filename)
    tbl = db.RPT_TABLE
    with db._connect() as conn:
        info.num = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        # get first/last record date
        info.date_range = [
            conn.execute(f"SELECT created FROM {tbl} WHERE id = {i}").fetchone()[0]
            for i in (1, info.num)
        ]
    _applog.debug(f"raw db info: {info}")
    return info


def _info_print(info: Info, stream: IOBase = None):
    """Print database summary information as aligned key/value lines.

    Args:
        info: Summary information to print.
        stream: Output stream. Defaults to `sys.stdout`, resolved at call time
            (not import time) so it can be redirected (e.g. by test capture).
    """
    if stream is None:
        stream = sys.stdout
    _print_aligned(
        stream,
        {
            "Database file": info.file,
            "Database version": f"{info.major_version}.{info.minor_version}",
            "Number of records": info.num,
            "First record created": time.asctime(time.gmtime(info.date_range[0])),
            "Last record created": time.asctime(time.gmtime(info.date_range[1])),
        },
    )


@dataclass
class SearchSpec:
    """Search specification"""

    time_min: str = field(
        default="", metadata={"doc": "Beginning of time range (YYY-MM-DD [hh:mm:ss])"}
    )
    time_max: str = field(
        default="", metadata={"doc": "End of time range (YYY-MM-DD [hh:mm:ss])"}
    )
    name_re: str = field(
        default="", metadata={"doc": "Name to match against (regular expression)"}
    )
    name_fixed: str = field(
        default="", metadata={"doc": "Name to match against (fixed string)"}
    )
    tags: str = field(default="", metadata={"doc": "Space-separated tags to match"})
    limit: int = field(
        default=100, metadata={"doc": "Maximum number of records to return"}
    )

    @classmethod
    def fields(cls) -> list[str]:
        """List the search fields as ``(name, type, help-text)`` tuples.

        Used to build the `view` subcommand's command-line options.

        Returns:
            One ``(name, type, doc)`` tuple per search field.
        """
        return [(f.name, f.type, f.metadata["doc"]) for f in dataclasses.fields(cls)]


def _view_command(args):
    """Run the `view` subcommand: print report records matching the filters.

    Args:
        args: Parsed command-line arguments (`db` plus the `SearchSpec` fields:
            time range, name filters, tags, limit).

    Raises:
        CommandError: If a filter value is invalid or the query fails.
    """
    dbfile = args.db
    if dbfile is None:
        db = init_report_db()
    else:
        db = ReportDB(dbfile)

    clauses = ["created >= ?", "created <= ?"]
    params = []
    if args.time_min:
        try:
            params.append(_parse_time(args.time_min))
        except ValueError as err:
            raise CommandError(
                "view", f"Bad time_min (expected ISO format time): {args.time_min}"
            )
    else:
        params.append(0.0)
    if args.time_max:
        try:
            params.append(_parse_time(args.time_max))
        except ValueError as err:
            raise CommandError(
                "view", f"Bad time_max (expected ISO format time): {args.time_max}"
            )
    else:
        params.append(9e9)
    if args.name_fixed:
        clauses.append("name = ?")
        params.append(args.name_fixed)
    name_pattern = None
    if args.name_re:
        try:
            name_pattern = re.compile(args.name_re)
        except re.error as err:
            raise CommandError("report", err)
        clauses.append("name REGEXP ?")
        params.append(args.name_re)
    if args.tags:
        tag_items = [t.lower() for t in args.tags.split()]
        tag_items.sort()
        clauses.append("tags LIKE ?")
        params.append("%" + "%".join(tag_items) + "%")
    limit = args.limit if args.limit is not None else SearchSpec.limit

    columns = [c[0] for c in ReportDB.RPT_COL if c[0] not in ("report", "hash")]
    columns_cs = ",".join(columns)
    query = f"SELECT {columns_cs} FROM {db.RPT_TABLE} WHERE {' AND '.join(clauses)}"
    query += " ORDER BY id ASC LIMIT ?"
    params.append(limit)
    _applog.debug(f"report query: {query} params={params}")

    def regexp(pattern, value):
        """SQLite REGEXP callback: True if `value` matches the compiled pattern."""
        return value is not None and name_pattern.search(value) is not None

    rows = []
    try:
        with db._connect() as conn:
            conn.create_function("REGEXP", 2, regexp)
            for row in conn.execute(query, params):
                row_dict = {}
                filedir, filename = None, None
                for i, item in enumerate(row):
                    col = columns[i]
                    # convert created timestamp to date string
                    if col == "created":
                        item = _time_string(item)
                    # pick out filedir/filename to be added later
                    elif col == "filedir":
                        filedir = item
                        continue
                    elif col == "filename":
                        filename = item
                        continue
                    row_dict[col] = item
                # add combined filedir/filename as 'file'
                row_dict["file"] = str(Path(filedir) / filename)
                # done; add row
                rows.append(row_dict)
    except (DBError, sqlite3.Error) as err:
        raise CommandError("report", err)
    # if any results at all, print as a table
    if rows:
        df = pd.DataFrame(rows)
        _view_print(sys.stdout, df)


def _view_print(stream: IOBase, df: pd.DataFrame):
    """Print report records as a plain-text table.

    Args:
        stream: Output stream to write to.
        df: DataFrame of report records to render.
    """
    stream.write(df.to_string(header=True, index=False))


# utility functions


def _print_aligned(stream: IOBase, kvp: dict[str, str], sep=":"):
    """Write key/value pairs with the separators aligned in a column.

    Args:
        stream: Output stream to write to.
        kvp: Mapping of labels to values.
        sep: Separator printed between each key and value.
    """
    key_max_len = 0
    for key in kvp:
        key_max_len = max(key_max_len, len(key))

    for key, value in kvp.items():
        spc = " " * (key_max_len - len(key))
        stream.write(f"{key}{spc} {sep} {value}\n")


def _time_string(t: float) -> str:
    """Format a Unix timestamp as a ``YYYY-MM-DD HH:MM:SS`` local-time string.

    Args:
        t: Unix timestamp (seconds).

    Returns:
        Formatted date/time string.
    """
    dt = datetime.datetime.fromtimestamp(t)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _parse_time(t: str) -> float:
    """Parse an ISO-format date/time string into a Unix timestamp.

    Args:
        t: ISO-format date/time (e.g. ``2026-01-31`` or ``2026-01-31 12:00:00``).

    Returns:
        Unix timestamp (seconds).

    Raises:
        ValueError: If `t` is not a valid ISO-format date/time.
    """
    parsed = datetime.datetime.fromisoformat(t)
    return parsed.timestamp()


# CLI
# ---
def _build_parser() -> argparse.ArgumentParser:
    """Build the `fi-db` argument parser with the `info` and `view` subcommands.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # info subcommand
    p = subparsers.add_parser("info", help="Show report database information")
    _add_parser_common(p)
    p.set_defaults(func=_info_command)

    # view subcommand
    p = subparsers.add_parser("view", help="View records in the database")
    _add_parser_common(p)
    for name, type_, doc in SearchSpec.fields():
        p.add_argument(
            f"--{name}",
            help=f"Search: {doc} ({type_.__name__})",
            type=type_,
            metavar="VALUE",
        )
    p.set_defaults(func=_view_command)

    return parser


def _add_parser_common(p: argparse.ArgumentParser):
    """Add the options shared by every subcommand (``--db``, ``--verbose``, ``--quiet``).

    Args:
        p: Subcommand parser to add the common arguments to.
    """
    p.add_argument("-d", "--db", metavar="PATH", help="Use this database file")
    p.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity"
    )
    p.add_argument(
        "-q", "--quiet", action="store_true", default=False, help="Suppress output"
    )


def _setup_logging(vb: int, quiet: bool):
    """Configure logging for the tool and the report-db module.

    Args:
        vb: Verbosity count (0=warning, 1=info, 2+=debug).
        quiet: If True, suppress all but critical messages (overrides `vb`).
    """
    global _applog

    _applog = logging.getLogger("idaes_fi.fi-db")
    dblog = logging.getLogger("idaes_fi.structfs.reportdb")
    if quiet:
        level = logging.CRITICAL
    else:
        if vb > 1:
            level = logging.DEBUG
        elif vb > 0:
            level = logging.INFO
        else:
            level = logging.WARNING
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    handler.setLevel(level)
    _applog.addHandler(handler)
    dblog.addHandler(handler)
    _applog.setLevel(level)


def main(args=None):
    """Entry point for the `fi-db` command-line tool.

    Args:
        args: Command-line arguments (defaults to `sys.argv` when None).

    Returns:
        Process exit code: 0 on success, -1 if a command failed.
    """
    status_code: int = 0
    parser = _build_parser()
    p = parser.parse_args(args=args)
    _setup_logging(p.verbose, p.quiet)
    try:
        p.func(p)
    except CommandError as err:
        print(f"ERROR: {err}")
        status_code = -1
    return status_code


if __name__ == "__main__":
    sys.exit(main())
