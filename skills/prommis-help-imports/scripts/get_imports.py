#!/usr/bin/env python3
"""
Search for a class in prommis, idaes, and pyomo and return
the correct import statement.

Usage:
    python get_imports.py <class_name>

Examples:
    python get_imports.py LeachingTrain
    python get_imports.py FlowsheetBlock
    python get_imports.py ConcreteModel

This script is designed to be run by Codex directly in the
appropriate conda environment. It does not ask the user to
run anything manually.
"""

import importlib
import inspect
import pkgutil
import sys
import warnings


# Suppress all warnings and non-critical errors during scanning
warnings.filterwarnings("ignore")


PACKAGES_TO_SEARCH = ["prommis", "idaes", "pyomo"]


def get_preferred_import(class_name: str, deep_module: str) -> str:
    """
    Check if the class is accessible from a shorter module path.
    If yes return the shorter path — it is the preferred import.
    If no return the original deep path.

    Example: Arc is defined in pyomo.network.arc but also accessible
    from pyomo.network — so pyomo.network is returned as the preferred
    import path since it is cleaner and more standard.
    """
    parts = deep_module.split(".")
    # try progressively shorter paths from second-shortest to longest
    # e.g. for pyomo.network.arc try pyomo.network then pyomo
    for i in range(len(parts) - 1, 0, -1):
        shorter_path = ".".join(parts[:i])
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                mod = importlib.import_module(shorter_path)
            if hasattr(mod, class_name):
                obj = getattr(mod, class_name)
                # make sure it is actually the same class
                if inspect.isclass(obj) and obj.__name__ == class_name:
                    return f"from {shorter_path} import {class_name}"
        except Exception:
            continue
    return f"from {deep_module} import {class_name}"


def search_package(package_name: str, class_name: str) -> list[str]:
    matches = []

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            package = importlib.import_module(package_name)
    except Exception:
        return []

    package_path = getattr(package, "__path__", None)
    if package_path is None:
        return []

    for _, module_name, _ in pkgutil.walk_packages(
        path=package_path,
        prefix=package_name + ".",
        onerror=lambda x: None,
    ):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                module = importlib.import_module(module_name)
        except Exception:
            continue

        try:
            if hasattr(module, class_name):
                obj = getattr(module, class_name)
                if inspect.isclass(obj) and obj.__module__ == module_name:
                    # get the preferred (shortest valid) import path
                    preferred = get_preferred_import(class_name, module_name)
                    if preferred not in matches:
                        matches.append(preferred)
        except Exception:
            continue

    return matches


def main():
    if len(sys.argv) < 2:
        print("Usage: python get_imports.py <class_name>")
        print("Example: python get_imports.py LeachingTrain")
        sys.exit(1)

    class_name = sys.argv[1]
    all_matches = []

    for package_name in PACKAGES_TO_SEARCH:
        matches = search_package(package_name, class_name)
        all_matches.extend(matches)

    # deduplicate while preserving order
    seen = set()
    unique_matches = []
    for match in all_matches:
        if match not in seen:
            seen.add(match)
            unique_matches.append(match)

    if not unique_matches:
        print(f"No match found for '{class_name}'.")
        print("Check that:")
        print("  1. The class name is spelled correctly")
        print("  2. The right conda environment is active")
        sys.exit(1)

    if len(unique_matches) == 1:
        print("Found 1 match:")
        print()
        print(unique_matches[0])
    else:
        print(f"Found {len(unique_matches)} matches:")
        print()
        for i, match in enumerate(unique_matches, 1):
            print(f"  {i}. {match}")

    sys.exit(0)


if __name__ in "__main__":
    main()