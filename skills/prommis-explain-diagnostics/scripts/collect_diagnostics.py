#!/usr/bin/env python
"""Collect runtime evidence from a FlowsheetRunner-wrapped flowsheet.

This command records facts and raw output. It does not diagnose root causes,
change the model, or choose a fix.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import importlib.util
import inspect
import io
import json
import platform
import re
import sys
import time
import traceback
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable


def _text(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return str(value)
    except Exception:
        return repr(value)


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {_text(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_value(item) for item in value]
    return _text(value)


def _exception_record(error: BaseException) -> dict[str, Any]:
    return {
        "module": type(error).__module__,
        "type": type(error).__name__,
        "message": _text(error),
        "traceback": traceback.format_exc(),
    }


def _capture(
    name: str, operation: Callable[[], Any]
) -> tuple[dict[str, Any], Any]:
    started = time.perf_counter()
    stdout = io.StringIO()
    stderr = io.StringIO()
    value = None
    error = None

    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            value = operation()
        status = "ok"
    except KeyboardInterrupt:
        raise
    except BaseException as caught:
        status = "error"
        error = _exception_record(caught)

    return (
        {
            "name": name,
            "status": status,
            "stdout": stdout.getvalue(),
            "stderr": stderr.getvalue(),
            "exception": error,
            "elapsed_seconds": round(time.perf_counter() - started, 6),
        },
        value,
    )


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _runtime_record() -> dict[str, Any]:
    packages = {}
    for distribution in ("idaes-pse", "pyomo", "idaes-fi"):
        version = _distribution_version(distribution)
        if version is not None:
            packages[distribution] = version

    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "packages": packages,
    }


def _import_target(path: Path) -> Any:
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
    module_name = f"_prommis_diagnostics_target_{digest}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create an import specification for {path}")

    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _has_public_attribute(value: Any, name: str) -> bool:
    try:
        inspect.getattr_static(value, name)
        return True
    except AttributeError:
        return False


def _looks_like_runner(value: Any) -> bool:
    if inspect.isclass(value):
        return False
    try:
        run_steps = getattr(value, "run_steps")
    except Exception:
        return False

    has_step_listing = any(
        callable(getattr(value, name, None))
        for name in ("get_defined_steps", "list_steps")
    )
    return (
        callable(run_steps)
        and has_step_listing
        and _has_public_attribute(value, "model")
        and _has_public_attribute(value, "results")
    )


def _defined_steps(runner: Any) -> list[str]:
    getter = getattr(runner, "get_defined_steps", None)
    if not callable(getter):
        getter = getattr(runner, "list_steps", None)
    if not callable(getter):
        return []
    return [_text(step) or "" for step in getter()]


def _runner_candidates(module: Any) -> list[dict[str, Any]]:
    candidates = []
    for name, value in vars(module).items():
        if not _looks_like_runner(value):
            continue
        steps = []
        steps_error = None
        try:
            steps = _defined_steps(value)
        except Exception as error:
            steps_error = {
                "module": type(error).__module__,
                "type": type(error).__name__,
                "message": _text(error),
            }
        candidates.append(
            {
                "name": name,
                "type": type(value).__name__,
                "module": type(value).__module__,
                "defined_steps": steps,
                "step_listing_error": steps_error,
                "object": value,
            }
        )
    return sorted(candidates, key=lambda item: item["name"])


def _public_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in candidate.items() if key != "object"}


def _select_runner(
    candidates: list[dict[str, Any]], requested_name: str | None
) -> tuple[dict[str, Any] | None, str]:
    if requested_name is not None:
        for candidate in candidates:
            if candidate["name"] == requested_name:
                return candidate, "selected"
        return None, "requested_runner_not_found"
    if len(candidates) == 1:
        return candidates[0], "selected"
    if not candidates:
        return None, "runner_not_found"
    return None, "runner_selection_required"


def _default_solver_probe() -> dict[str, Any]:
    from idaes.core.solvers import get_solver

    solver = get_solver()
    record = {
        "type": type(solver).__name__,
        "module": type(solver).__module__,
        "available": None,
        "version": None,
        "executable": None,
    }

    available = getattr(solver, "available", None)
    if callable(available):
        record["available"] = bool(available(exception_flag=False))

    version = getattr(solver, "version", None)
    if callable(version):
        record["version"] = _json_value(version())

    executable = getattr(solver, "executable", None)
    if callable(executable):
        record["executable"] = _text(executable())

    return record


def _result_is_present(results: Any) -> bool:
    if results is None:
        return False
    if isinstance(results, Mapping):
        return bool(results)
    return True


def _solver_result_record(results: Any) -> dict[str, Any]:
    if not _result_is_present(results):
        return {"present": False}

    record = {"present": True}
    solver = getattr(results, "solver", None)
    if solver is None:
        record["solver_section_present"] = False
        return record

    record["solver_section_present"] = True
    for field in ("status", "termination_condition", "message"):
        try:
            value = getattr(solver, field)
        except Exception:
            value = None
        record[field] = _json_value(value)

    try:
        from pyomo.opt import check_optimal_termination

        record["check_optimal_termination"] = bool(
            check_optimal_termination(results)
        )
    except Exception as error:
        record["check_optimal_termination"] = None
        record["optimality_check_error"] = {
            "module": type(error).__module__,
            "type": type(error).__name__,
            "message": _text(error),
        }
    return record


def _suggested_methods(output: str, toolbox: Any) -> list[str]:
    suggestions = []
    for name in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", output):
        if name in suggestions or name.startswith("_"):
            continue
        try:
            method = getattr(toolbox, name)
        except Exception:
            continue
        if callable(method):
            suggestions.append(name)
    return suggestions


def _prepare_runner_output_capture(runner: Any) -> dict[str, Any]:
    """Use the collector's capture instead of the runner's optional capture action.

    Some FlowsheetRunner versions can mask the original step exception while
    flushing their solver-output action. The collector already captures stdout
    and stderr for the whole run, so removing that action through the public
    runner API avoids duplicate capture and preserves the original exception.
    """

    get_action = getattr(runner, "get_action", None)
    remove_action = getattr(runner, "remove_action", None)
    if not callable(get_action) or not callable(remove_action):
        return {"removed": False, "reason": "Runner has no public action API."}

    try:
        from idaes_fi.structfs.fsrunner import ActionNames

        action_name = ActionNames.SOLVER_OUTPUT.value
    except (ImportError, AttributeError):
        return {
            "removed": False,
            "reason": "Installed runner does not expose a solver-output action name.",
        }

    try:
        action = get_action(action_name)
    except KeyError:
        return {"removed": False, "reason": "No solver-output action is installed."}

    remove_action(action_name)
    return {
        "removed": True,
        "action_name": action_name,
        "action_type": type(action).__name__,
    }


def _run_kwargs(arguments: argparse.Namespace) -> dict[str, Any]:
    # FlowsheetRunner places its configured tee value in the public Context.
    # Pass only supported step-boundary arguments to run_steps().
    kwargs: dict[str, Any] = {}
    for name in ("first", "last", "before", "after"):
        value = getattr(arguments, name)
        if value is not None:
            kwargs[name] = value
    return kwargs


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Collect runtime, runner, solver-result, and IDAES diagnostics "
            "evidence from a wrapped flowsheet."
        )
    )
    parser.add_argument("flowsheet", help="Path to the wrapped flowsheet file")
    parser.add_argument(
        "--runner", help="Module variable name when more than one runner is present"
    )
    parser.add_argument(
        "--skip-run", action="store_true", help="Discover the runner without executing steps"
    )
    start_group = parser.add_mutually_exclusive_group()
    start_group.add_argument("--first", help="First runner step to execute")
    start_group.add_argument("--after", help="Begin after this runner step")
    end_group = parser.add_mutually_exclusive_group()
    end_group.add_argument("--last", help="Last runner step to execute")
    end_group.add_argument("--before", help="Stop before this runner step")
    parser.add_argument(
        "--numerical",
        choices=("auto", "yes", "no"),
        default="auto",
        help=(
            "Run numerical diagnostics automatically on any retained model, "
            "force them when a model exists, or never"
        ),
    )
    parser.add_argument(
        "--probe-solver",
        action="store_true",
        help="Probe the IDAES default solver only when version details are needed",
    )
    parser.add_argument(
        "--follow-up",
        help=(
            "Run one exact DiagnosticsToolbox method named by the current "
            "standard report"
        ),
    )
    parser.add_argument("--output", help="Optional path for a copy of the JSON report")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output")
    parser.add_argument(
        "--quiet", action="store_true", help="Do not print the JSON report to stdout"
    )
    return parser


def _finish_report(report: dict[str, Any], started: float) -> dict[str, Any]:
    report["elapsed_seconds"] = round(time.perf_counter() - started, 6)
    return report


def collect(arguments: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    target = Path(arguments.flowsheet).expanduser().resolve()
    report: dict[str, Any] = {
        "schema_version": 2,
        "collector": "collect_diagnostics",
        "target": str(target),
        "runtime": _runtime_record(),
        "outcome": "collecting",
        "phases": [],
        "runner": None,
        "solver_probe": None,
        "solver_result": {"present": False},
        "diagnostics": None,
    }

    if not target.is_file():
        report["outcome"] = "target_not_found"
        report["input_error"] = f"Flowsheet file does not exist: {target}"
        return _finish_report(report, started)

    if arguments.probe_solver:
        solver_phase, solver_probe = _capture(
            "default_solver_probe", _default_solver_probe
        )
        report["phases"].append(solver_phase)
        report["solver_probe"] = solver_probe

    import_phase, module = _capture("target_import", lambda: _import_target(target))
    report["phases"].append(import_phase)
    if import_phase["status"] != "ok":
        report["outcome"] = "import_failed"
        return _finish_report(report, started)

    discovery_phase, candidates = _capture(
        "runner_discovery", lambda: _runner_candidates(module)
    )
    report["phases"].append(discovery_phase)
    if discovery_phase["status"] != "ok":
        report["outcome"] = "runner_discovery_failed"
        return _finish_report(report, started)

    selected, selection_status = _select_runner(candidates, arguments.runner)
    report["runner"] = {
        "selection_status": selection_status,
        "requested_name": arguments.runner,
        "candidates": [_public_candidate(item) for item in candidates],
        "selected": _public_candidate(selected) if selected is not None else None,
    }
    if selected is None:
        report["outcome"] = selection_status
        return _finish_report(report, started)

    runner = selected["object"]
    capture_setup_phase, capture_setup = _capture(
        "runner_output_capture_setup",
        lambda: _prepare_runner_output_capture(runner),
    )
    report["phases"].append(capture_setup_phase)
    report["runner"]["output_capture_setup"] = capture_setup
    run_kwargs = _run_kwargs(arguments)
    report["runner"]["run_request"] = {
        "skip_run": bool(arguments.skip_run),
        "arguments": run_kwargs,
    }

    run_phase = None
    if not arguments.skip_run:
        run_phase, _ = _capture(
            "runner_execution", lambda: runner.run_steps(**run_kwargs)
        )
        report["phases"].append(run_phase)

    def runner_state() -> tuple[Any, Any, Any, Any]:
        return (
            runner.model,
            runner.results,
            getattr(runner, "failed", None),
            getattr(runner, "failed_actions", None),
        )

    state_phase, state = _capture("runner_state", runner_state)
    report["phases"].append(state_phase)
    if state_phase["status"] == "ok":
        model, results, runner_failed, failed_actions = state
    else:
        model, results, runner_failed, failed_actions = None, None, None, None

    report["runner"]["model_present"] = model is not None
    report["runner"]["reported_failed"] = _json_value(runner_failed)
    report["runner"]["failed_actions"] = _json_value(failed_actions)
    report["solver_result"] = _solver_result_record(results)
    run_failed = run_phase is not None and (
        run_phase["status"] == "error" or runner_failed is True
    )

    if model is None:
        report["diagnostics"] = {
            "status": "skipped",
            "reason": "No model is available from the selected runner.",
        }
    else:
        diagnostics: dict[str, Any] = {
            "status": "collecting",
            "structural": None,
            "numerical": None,
            "suggested_methods": [],
            "follow_up": None,
            "evidence_scope": (
                "partial_model_after_failed_run"
                if run_failed
                else "completed_model"
            ),
        }

        def create_toolbox() -> Any:
            from idaes.core.util import DiagnosticsToolbox

            return DiagnosticsToolbox(model)

        setup_phase, toolbox = _capture("diagnostics_setup", create_toolbox)
        report["phases"].append(setup_phase)
        if setup_phase["status"] != "ok":
            diagnostics["status"] = "setup_failed"
            report["diagnostics"] = diagnostics
        else:
            structural_method = getattr(toolbox, "report_structural_issues", None)
            if callable(structural_method):
                structural_phase, _ = _capture(
                    "diagnostics_structural", structural_method
                )
                report["phases"].append(structural_phase)
                diagnostics["structural"] = structural_phase
                diagnostics["suggested_methods"].extend(
                    _suggested_methods(
                        structural_phase["stdout"] + structural_phase["stderr"],
                        toolbox,
                    )
                )
            else:
                diagnostics["structural"] = {
                    "status": "unavailable",
                    "reason": "The installed toolbox has no callable structural report.",
                }

            run_numerical = arguments.numerical != "no"
            if run_numerical and run_failed:
                partial_checks: dict[str, Any] = {
                    "status": "partial_checks_collected",
                    "reason": (
                        "The full numerical report was not run on the partial "
                        "model. Safe focused checks were run instead."
                    ),
                }
                for key, method_name, phase_name in (
                    (
                        "variables_with_none_values",
                        "display_variables_with_none_value_in_activated_constraints",
                        "diagnostics_partial_none_values",
                    ),
                    (
                        "variables_at_or_outside_bounds",
                        "display_variables_at_or_outside_bounds",
                        "diagnostics_partial_bounds",
                    ),
                ):
                    method = getattr(toolbox, method_name, None)
                    if callable(method):
                        check_phase, _ = _capture(phase_name, method)
                        report["phases"].append(check_phase)
                        partial_checks[key] = {
                            "method": method_name,
                            **check_phase,
                        }
                    else:
                        partial_checks[key] = {
                            "status": "unavailable",
                            "method": method_name,
                            "reason": (
                                "The installed toolbox has no callable "
                                f"{method_name} method."
                            ),
                        }
                diagnostics["numerical"] = partial_checks
            elif run_numerical:
                numerical_method = getattr(toolbox, "report_numerical_issues", None)
                if callable(numerical_method):
                    numerical_phase, _ = _capture(
                        "diagnostics_numerical", numerical_method
                    )
                    report["phases"].append(numerical_phase)
                    diagnostics["numerical"] = numerical_phase
                    for method_name in _suggested_methods(
                        numerical_phase["stdout"] + numerical_phase["stderr"],
                        toolbox,
                    ):
                        if method_name not in diagnostics["suggested_methods"]:
                            diagnostics["suggested_methods"].append(method_name)
                else:
                    diagnostics["numerical"] = {
                        "status": "unavailable",
                        "reason": "The installed toolbox has no callable numerical report.",
                    }
            else:
                diagnostics["numerical"] = {
                    "status": "skipped",
                    "reason": "Numerical diagnostics were disabled with --numerical no.",
                }

            if arguments.follow_up is None:
                diagnostics["follow_up"] = {"status": "not_requested"}
            elif arguments.follow_up not in diagnostics["suggested_methods"]:
                diagnostics["follow_up"] = {
                    "status": "not_suggested",
                    "method": arguments.follow_up,
                    "reason": (
                        "The method was not named by the current standard "
                        "DiagnosticsToolbox reports."
                    ),
                }
            else:
                follow_up = getattr(toolbox, arguments.follow_up, None)
                if not callable(follow_up):
                    diagnostics["follow_up"] = {
                        "status": "unavailable",
                        "method": arguments.follow_up,
                    }
                else:
                    signature = inspect.signature(follow_up)
                    required = [
                        parameter.name
                        for parameter in signature.parameters.values()
                        if parameter.default is inspect.Parameter.empty
                        and parameter.kind
                        in (
                            inspect.Parameter.POSITIONAL_ONLY,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                            inspect.Parameter.KEYWORD_ONLY,
                        )
                    ]
                    if required:
                        diagnostics["follow_up"] = {
                            "status": "unsupported_signature",
                            "method": arguments.follow_up,
                            "signature": str(signature),
                            "required_arguments": required,
                        }
                    else:
                        follow_up_phase, _ = _capture(
                            "diagnostics_follow_up", follow_up
                        )
                        report["phases"].append(follow_up_phase)
                        diagnostics["follow_up"] = {
                            "method": arguments.follow_up,
                            "signature": str(signature),
                            "documentation": inspect.getdoc(follow_up),
                            **follow_up_phase,
                        }

            diagnostics["status"] = "collected"
            diagnostics["timing"] = (
                "without_runner_execution"
                if arguments.skip_run
                else "after_requested_runner_execution"
            )
            report["diagnostics"] = diagnostics

    if run_failed:
        report["outcome"] = "run_failed_with_evidence"
    else:
        report["outcome"] = "collected"
    return _finish_report(report, started)


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    report = collect(arguments)
    indent = 2 if arguments.pretty else None
    encoded = json.dumps(report, indent=indent, ensure_ascii=False)

    if arguments.output:
        output_path = Path(arguments.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(encoded + "\n", encoding="utf-8")

    if not arguments.quiet:
        print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
