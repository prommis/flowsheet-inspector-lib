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
Git utility code
"""

from pathlib import Path
import subprocess


def git_repo_root(file_path: str) -> Path | None:
    """Return the root directory of the Git repo containing file_path.

    Args:
        file_path: File of interest

    Returns:
        Directory, or None if there was an error from the Git command
    """
    path = Path(file_path).resolve()

    try:
        root = subprocess.check_output(
            ["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return None

    return Path(root)


def git_head_hash(file_path: str | Path) -> str | None:
    """Return current commit hash for the Git repo containing file_path.

    Args:
        file_path: File of interest

    Returns:
        Hash, or None if there was an error from the Git command
    """
    path = Path(file_path).resolve()

    try:
        hash = subprocess.check_output(
            ["git", "-C", str(path.parent), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        hash = None

    return hash


if __name__ == "__main__":
    import sys

    file = sys.argv[1]

    print("repo root:", git_repo_root(file))
    print("head hash:", git_head_hash(file))
