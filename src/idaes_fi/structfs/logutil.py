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
Utility functions for logging
"""

import logging
import warnings

g_quiet = {}


def quiet(roots=("idaes", "pyomo"), level=logging.CRITICAL):
    """Be very quiet. I'm hunting wabbits.

    Ignore warnings and set all loggers starting with one of
    the values in 'roots' to the given level (default=CRITICAL).
    """
    warnings.filterwarnings("ignore")
    all_loggers = [logging.getLogger()] + [
        logging.getLogger(name) for name in logging.root.manager.loggerDict
    ]
    for lg in all_loggers:
        for root in roots:
            if lg.name.startswith(root + "."):
                g_quiet[lg.name] = lg.level
                lg.setLevel(level)


def unquiet():
    """Reverse previous quiet()"""
    for k in list(g_quiet.keys()):
        v = g_quiet[k]
        lg = logging.getLogger(k)
        lg.setLevel(v)
        del g_quiet[k]


def init_fi():
    """Initialize logging for flowsheet inspector"""
    log = logging.getLogger("idaes_fi")
    if not log.hasHandlers():
        h = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        h.setFormatter(fmt)
        log.addHandler(h)
