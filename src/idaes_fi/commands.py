"""
CLI commands.

All commands are sub-commands of the command named in
MAIN_COMMAND.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from idaes_fi.api import init_report_db, load_module, get_module_flowsheet_runners
from idaes_fi.reportdb import ReportDB
from idaes_fi.reportdb_migrate import MigrationStrategy, MigrationError

__author__ = "Dan Gunter (LBNL)"

# logging.basicConfig()
_h = logging.StreamHandler()
logging.getLogger("idaes_fi.commands").addHandler(_h)
_h.setFormatter(
    logging.Formatter("[%(levelname)s] (%(asctime)s) %(name)s - %(message)s")
)
_log = logging.getLogger("idaes_fi.commands")

# Package name, for help/descriptions
PKG = "IDAES Flowsheet Inspector"

# Main command.
# Stands for "IDAES Flowsheet Inspector"
# Should match value in pyproject.toml under [project.scripts]
MAIN_COMMAND = "ifi"


# ----
# Database commands
# ----


def _get_db(filename: Optional[str] = None) -> ReportDB:
    if filename is None:
        db = init_report_db()
    else:
        db = ReportDB(filename)
    return db


def db_migrate(filename: Optional[str] = None):
    db = _get_db(filename)
    ms = MigrationStrategy()
    return ms.migrate(db.filename)


def _db_migrate_cli(args) -> bool:
    try:
        print("Migrating database..")
        did_something = db_migrate(args.file)
    except MigrationError as err:
        print(f"Migration not performed: {err}")
        return False
    if did_something:
        print("Success!")
    else:
        print("Nothing to do, database is already latest version")
    return True


def db_info(filename: Optional[str] = None):
    db = _get_db(filename)
    rdb_ver = ReportDB.MAJOR_VERSION, ReportDB.MINOR_VERSION
    return {"file": db.filename, "version": db.version, "lib_version": rdb_ver}


def _db_info_cli(args) -> bool:
    info = db_info(args.file)
    if args.json:
        json.dump(info, sys.stdout, indent=2, cls=PathJSONEncoder)
    else:
        w = max((len(s) for s in info))
        for k, v in info.items():
            name = k.rjust(w)
            if k.endswith("version"):
                v = f"{v[0]}.{v[1]}"
            print(f"{name}: {v}")
    return True


# ----
# Flowsheet commands
# ----


def _get_fs_runners(modulename: str | None, filename: str | None):
    if modulename is None and filename is None:
        raise ValueError("Cannot load flowsheet: both module and file are empty")
    try:
        mod = load_module(name=modulename, path=filename)
    except ImportError as err:
        which = modulename if modulename else filename
        raise ValueError(f"Could not import flowsheet '{which}': {err}")
    return get_module_flowsheet_runners(mod)


def flowsheet_run(
    module: Optional[str] = None,
    file: Optional[str] = None,
    name: Optional[str] = None,
    last_step: Optional[str] = None,
    level: Optional[int] = None,
    nodb: bool = False,
):
    flowsheets = _get_fs_runners(module, file)
    if name is not None:
        if name not in flowsheets:
            raise ValueError(f"Flowsheet '{name}' not found")
        flowsheet = flowsheets[name]
    else:
        keys = sorted(flowsheets.keys())
        flowsheet = flowsheets[keys[0]]
    if last_step is not None:
        flowsheet.last_step = last_step
    if level is not None:
        flowsheet.log_level = level
    if nodb:
        _log.info("Not using report database")
        flowsheet.report_db_off()
    flowsheet.run_flowsheet()


def _flowsheet_run_cli(args):
    if args.module is None and args.file is None:
        print("Must set --module or --file")
        return False
    try:
        flowsheet_run(
            module=args.module,
            file=args.file,
            name=args.name,
            level=args.level,
            last_step=args.last_step,
            nodb=args.no_db,
        )
    except Exception as err:
        print(f"Could not run flowsheet: {err}")
        if args.level >= logging.INFO:
            import traceback

            print("Traceback:")
            traceback.print_exc()
        else:
            print("Increase verbosity to see the full traceback")
        return False
    return True


def flowsheet_steps(
    module: Optional[str] = None,
    file: Optional[str] = None,
):
    flowsheets = _get_fs_runners(module, file)
    return {k: v.steps for k, v in flowsheets.items()}


def _flowsheet_steps_cli(args):
    _log.debug(
        "Fetching flowsheet steps for module=%s, file=%s", args.module, args.file
    )
    if args.module is None and args.file is None:
        print("Must set --module or --file")
        return False
    try:
        steps = flowsheet_steps(module=args.module, file=args.file)
    except Exception as err:
        print(f"Could not load flowsheets to extract steps.\nReason: {err}")
        return False
    if args.json:
        json.dump(steps, sys.stdout)
    else:
        for fs_name, fs_steps in steps.items():
            print(f"{fs_name}: {', '.join(fs_steps)}")
    _log.debug("Fetched flowsheet steps: %s", steps)
    return True


# ----
# Utilities
# ----


class PathJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


class LogLevelAction(argparse.Action):
    """Parse a case-insensitive logging level name."""

    _levels = {
        "NOTSET": logging.NOTSET,
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARN": logging.WARNING,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "FATAL": logging.CRITICAL,
        "CRITICAL": logging.CRITICAL,
    }

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            level = self._levels[values.upper()]
        except (AttributeError, KeyError):
            choices = ", ".join(self._levels)
            raise argparse.ArgumentError(
                self,
                f"invalid log level: {values!r} (choose from {choices})",
            )
        setattr(namespace, self.dest, level)


# ----
# Main entry point
# ----


def main(*cmdline):
    p = argparse.ArgumentParser(f"{PKG}")
    p_subp = p.add_subparsers()
    # global options
    p.add_argument(
        "--json",
        "-J",
        action="store_true",
        help="Format output as JSON (default=plain text)",
    )
    p.add_argument(
        "-v", "--verbose", help="Increase output verbosity", action="count", default=0
    )

    # add 'db' subcommand and sub-subcommands
    dbp = p_subp.add_parser("db")
    dbp_subp = dbp.add_subparsers()
    # db migrate
    desc = "Migrate to latest database version"
    cmd = dbp_subp.add_parser("migrate", help=desc, description=desc)
    cmd.set_defaults(func=_db_migrate_cli)
    cmd.add_argument("--file", "-f", help="Database file (instead of default)")
    # db version
    desc = "Show current database information"
    cmd = dbp_subp.add_parser("info", help=desc, description=desc)
    cmd.add_argument("--file", "-f", help="Database file (instead of default)")
    cmd.set_defaults(func=_db_info_cli)

    # add 'flowsheet' subcommand and sub-subcommands
    runp = p_subp.add_parser("flowsheet")
    runp.add_argument(
        "--level",
        "-L",
        help="Set logging level for flowsheet runner",
        action=LogLevelAction,
        default=logging.INFO,
    )
    run_subp = runp.add_subparsers()
    # run flowsheet
    desc = "Run flowsheet"
    cmd = run_subp.add_parser("run", help=desc, description=desc)
    cmd.add_argument("--file", "-f", help="Flowsheet Python file")
    cmd.add_argument("--module", "-m", help="Flowsheet Python module name")
    cmd.add_argument("--name", "-n", help="Flowsheet variable name")
    cmd.add_argument(
        "--last-step", "-l", help="Flowsheet step at which to stop the run"
    )
    cmd.add_argument(
        "--no-db",
        action="store_true",
        help="Do not use the report database",
    )
    cmd.set_defaults(func=_flowsheet_run_cli)
    # get steps for flowsheet
    desc = "Get defined steps for flowsheet(s)"
    cmd = run_subp.add_parser("steps", help=desc, description=desc)
    cmd.add_argument("--file", "-f", help="Flowsheet Python file")
    cmd.add_argument("--module", "-m", help="Flowsheet Python module name")
    cmd.set_defaults(func=_flowsheet_steps_cli)

    if cmdline:
        args = p.parse_args(*cmdline)
    else:
        args = p.parse_args()

    # handle verbosity
    if hasattr(args, "verbose"):
        if args.verbose == 1:
            logging.getLogger().setLevel(logging.INFO)
        elif args.verbose >= 2:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.WARNING)

    # e.g. "ifi flowsheet" without a further subcommand
    if not hasattr(args, "func"):
        p.print_help()
        return 1

    success = args.func(args)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
