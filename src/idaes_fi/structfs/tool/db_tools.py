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
implemented by module `idaes_fi.structfs.reportdb`.
"""

import argparse
from dataclasses import dataclass
from io import IOBase
import logging
from pathlib import Path
import sys
import time

from idaes_fi.structfs.reportdb import ReportDB, DBError
from idaes_fi.structfs.runner import Runner

_log = logging.getLogger(__name__)


class CommandError(Exception):
    def __init__(self, command: str, error: str):
        msg = f"in command '{command}': {error}"
        super().__init__(msg)


@dataclass
class Info:
    file: Path = None
    major_version: int = 0
    minor_version: int = 0
    num: int = 0
    date_range: list[float] = (0, 0)


def _info_command(args):
    dbfile = args.db
    if dbfile is None:
        db = Runner.get_default_report_db()
    else:
        db = ReportDB(dbfile)
    try:
        info = _info_fetch(db)
    except DBError as err:
        raise CommandError("info", err)
    _info_print(info)


def _info_fetch(db: ReportDB):
    _applog.info(f"query database '{db.filename}'")
    info = Info()
    info.major_version, info.minor_version = db.version
    info.file = Path(db.filename)
    tbl = db.TABLE
    with db._connect() as conn:
        info.num = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        # get first/last record date
        info.date_range = [
            conn.execute(f"SELECT created FROM {tbl} WHERE id = {i}").fetchone()[0]
            for i in (1, info.num)
        ]
    _applog.debug(f"raw db info: {info}")
    return info


def _info_print(info: Info, stream: IOBase = sys.stdout):
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


def _report_command(args):
    print("Not yet implemented")


# utility functions


def _print_aligned(stream: IOBase, kvp: dict[str, str], sep=":"):
    key_max_len = 0
    for key in kvp:
        key_max_len = max(key_max_len, len(key))

    for key, value in kvp.items():
        spc = " " * (key_max_len - len(key))
        stream.write(f"{key}{spc} {sep} {value}\n")


# CLI
# ---
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # add info subcommand
    p = subparsers.add_parser("info", help="Show report database information")
    _add_parser_common(p)
    p.set_defaults(func=_info_command)

    # add dump subcommand
    p = subparsers.add_parser("report", help="Get a report from the database")
    _add_parser_common(p)
    p.set_defaults(func=_report_command)

    return parser


def _add_parser_common(p: argparse.ArgumentParser):
    p.add_argument("-d", "--db", metavar="PATH", help="Use this database file")
    p.add_argument(
        "-v", "--verbose", action="count", default=0, help="Increase verbosity"
    )
    p.add_argument(
        "-q", "--quiet", action="store_true", default=False, help="Suppress output"
    )


def _setup_logging(vb: int, quiet: bool):
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
