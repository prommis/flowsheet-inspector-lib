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
# in the Software to reproduce, distribute copies to the public, prepare derivative works, perform
# publicly and display publicly, and to permit other to do so.
#
#################################################################################
"""Git hash action for flowsheet runner runs."""

# stdlib
import inspect
from pathlib import Path

# third-party
from pydantic import BaseModel

# package
from ...gitutil import git_head_hash
from ..action_base import Action


class GitHash(Action):
    """Capture the HEAD hash of the repository containing the given path."""

    class Report(BaseModel):
        """Report returned by :meth:`report`."""

        hash: str | None = None

    def __init__(self, runner, file_path: Path | None = None, **kwargs):
        super().__init__(runner, **kwargs)
        self._path = file_path
        self._hash: str | None = None

    def after_run(self):
        """Capture the repository hash after a run completes."""
        if self._path is not None:
            self._hash = git_head_hash(self._path)

    def report(self) -> Report:
        """Return the captured repository hash."""
        return self.Report(hash=self._hash)
