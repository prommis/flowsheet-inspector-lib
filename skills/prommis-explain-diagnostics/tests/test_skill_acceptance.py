"""Acceptance-contract tests for the friendly diagnostics workflow."""

from __future__ import annotations

from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_TEXT = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
DIAGNOSTICS_TEXT = (
    SKILL_ROOT / "references" / "diagnostics-guide.md"
).read_text(encoding="utf-8")
IPOPT_TEXT = (SKILL_ROOT / "references" / "ipopt-guide.md").read_text(
    encoding="utf-8"
)
RUNNER_TEXT = (
    SKILL_ROOT / "references" / "step-runner-guide.md"
).read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    lines = (line.removeprefix("> ") for line in text.splitlines())
    return " ".join(" ".join(lines).split())


def _section(start: str, end: str) -> str:
    return SKILL_TEXT.split(start, maxsplit=1)[1].split(end, maxsplit=1)[0]


@pytest.mark.unit
def test_named_flowsheet_runs_complete_sequence_without_second_permission() -> None:
    stage = _normalized(_section("## Stage 1 â€” run the flowsheet", "## Stage 2"))

    assert "authorizes one complete local, read-only run" in stage
    assert "Do not ask for permission again" in stage
    assert "Running your flowsheet now" in stage
    assert "scripts/collect_diagnostics.py" in stage
    assert "execute the full registered sequence" in stage
    assert "report_structural_issues()" in stage
    assert "report_numerical_issues()" in stage
    assert "retain partial model state after a failure" in stage


@pytest.mark.unit
def test_stage_two_restores_compact_plain_english_contract() -> None:
    stage = _normalized(_section("## Stage 2", "## Stage 3"))

    for required in (
        "Stage 2 â€” here is what I found.",
        "Solver output:",
        "Diagnostics output:",
        "What this means:",
        "Fix:",
        "minor cautions",
    ):
        assert required in stage

    for hidden in (
        "IPOPT iteration tables",
        "full model statistics",
        "full tracebacks",
        "raw caution details",
    ):
        assert hidden in stage


@pytest.mark.unit
@pytest.mark.parametrize(
    ("message", "translation"),
    (
        ("Optimal Solution Found", "The flowsheet solved successfully."),
        (
            "local infeasibility",
            "could not find values that satisfy all active equations and bounds",
        ),
        (
            "Maximum Number of Iterations Exceeded",
            "The flowsheet stopped before finding a solution.",
        ),
        (
            "Restoration Failed",
            "could not recover a set of values that satisfies its equations",
        ),
        (
            "Error in AMPL Evaluation",
            "A calculation received an invalid value",
        ),
    ),
)
def test_ipopt_guide_contains_user_facing_translations(
    message: str, translation: str
) -> None:
    assert message in IPOPT_TEXT
    assert translation in IPOPT_TEXT


@pytest.mark.unit
@pytest.mark.parametrize(
    "warning",
    (
        "Degrees of Freedom is not zero",
        "Structural singularity",
        "Potential evaluation errors",
        "Variables at or outside bounds",
        "Constraints with large residuals",
        "Variables with extreme values",
        "Unit consistency",
    ),
)
def test_diagnostics_guide_restores_warning_explanations(warning: str) -> None:
    assert warning in DIAGNOSTICS_TEXT


@pytest.mark.unit
def test_next_step_is_one_verified_report_method_and_then_stop() -> None:
    stage = _normalized(_section("## Stage 3", "## Fix and verification loop"))

    assert "Prefer the exact method named" in stage
    assert "inspect its signature" in stage
    assert "Can I run dt.<method>()" in stage
    assert "then stop" in stage
    assert "Do not run multiple follow-ups" in stage
    assert "--follow-up <method>" in stage


@pytest.mark.unit
def test_fix_loop_offers_user_and_codex_paths_and_verifies() -> None:
    loop = _normalized(
        _section("## Fix and verification loop", "## Stopping conditions")
    )

    assert "Want me to fix this, or will you do it?" in loop
    assert "If I fix it" in loop
    assert "If you fix it" in loop
    assert "Preserve unrelated edits" in loop
    assert "Run the complete flowsheet again" in loop
    assert "resolved, improved, unchanged, worsened, or not comparable" in loop


@pytest.mark.unit
def test_runner_reference_requires_full_run_and_concise_output() -> None:
    runner = _normalized(RUNNER_TEXT)

    assert "executes every registered step in order" in runner
    assert "captures console output, including solver output" in runner
    assert "Stage 2 â€” here is what I found" in runner
    assert "Can I run dt.<method>()" in runner
    assert "Do not show full IPOPT iteration tables" in runner


@pytest.mark.unit
def test_runtime_selection_is_not_hardcoded() -> None:
    for environment in ("conda run -n", "prommis-dev", "idaes-fi"):
        assert environment not in SKILL_TEXT
