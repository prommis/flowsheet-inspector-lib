"""Run evals for the PrOMMiS skill catalog."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


THIS_FILE = Path(__file__).resolve()
EVAL_ROOT = THIS_FILE.parent
PROJECT_ROOT = THIS_FILE.parents[2]

SKILL_SEARCH_ROOT = PROJECT_ROOT / "skill-search"
SKILLS_ROOT = PROJECT_ROOT / "skills"

CASES_ROOT = EVAL_ROOT / "cases"
FIXTURES_ROOT = EVAL_ROOT / "fixtures"
VALIDATORS_ROOT = EVAL_ROOT / "validators"

ROUTING_CASES_FILE = CASES_ROOT / "routing_cases.json"
ACTION_CASES_FILE = CASES_ROOT / "action_cases.json"

sys.path.insert(0, str(SKILL_SEARCH_ROOT))

from skill_search import search_skills  # noqa: E402


def load_cases(cases_file: Path) -> list[dict[str, str]]:
    """Load eval cases from JSON."""
    text = cases_file.read_text(encoding="utf-8-sig")
    return json.loads(text)


def find_case(cases_file: Path, case_id: str) -> dict[str, str]:
    """Find one eval case by id."""
    for case in load_cases(cases_file):
        if case["id"] == case_id:
            return case

    raise ValueError(f"Case id not found in {cases_file}: {case_id}")


def run_routing_eval(cases_file: Path, top_k: int) -> int:
    """Run each routing case and return the number of failures."""
    failures = 0

    for case in load_cases(cases_file):
        prompt = case["prompt"]
        expected_skill = case["expected_skill"]

        matches = search_skills(SKILLS_ROOT, query=prompt, top_k=top_k)
        ranked_skill_names = [match.skill.name for match in matches]
        top_skill = ranked_skill_names[0] if ranked_skill_names else None

        if top_skill == expected_skill:
            print(f"PASS {case['id']}: {expected_skill}")
            continue

        print(f"FAIL {case['id']}: expected {expected_skill}, got {top_skill}")
        print(f"  prompt: {prompt}")
        print(f"  ranked: {ranked_skill_names}")
        failures += 1

    return failures


def prepare_action_workspace(case: dict[str, str], workspace: Path) -> None:
    """Copy a fixture into a fresh workspace and write the prompt."""
    fixture = FIXTURES_ROOT / case["fixture"]

    if not fixture.is_dir():
        raise FileNotFoundError(f"Missing fixture directory: {fixture}")

    if workspace.exists():
        raise FileExistsError(f"Workspace already exists: {workspace}")

    workspace.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(fixture, workspace)

    prompt_file = workspace / "PROMPT.txt"
    prompt_file.write_text(case["prompt"] + "\n", encoding="utf-8")


def validate_action_workspace(case: dict[str, str], workspace: Path) -> int:
    """Run the validator for an action eval workspace."""
    validator = VALIDATORS_ROOT / case["validator"]

    if not workspace.is_dir():
        raise FileNotFoundError(f"Missing workspace: {workspace}")

    if not validator.is_file():
        raise FileNotFoundError(f"Missing validator: {validator}")

    command = [
        sys.executable,
        str(validator),
        "--workspace",
        str(workspace),
        "--input-file",
        case["input_file"],
        "--output-file",
        case["output_file"],
    ]
    result = subprocess.run(command, check=False)
    return result.returncode


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description="Run PrOMMiS skill evals.")
    parser.add_argument(
        "--mode",
        choices=("routing", "prepare-action", "validate-action"),
        default="routing",
        help="Eval mode to run.",
    )
    parser.add_argument(
        "--routing-cases",
        default=ROUTING_CASES_FILE,
        type=Path,
        help="Path to the routing cases JSON file.",
    )
    parser.add_argument(
        "--action-cases",
        default=ACTION_CASES_FILE,
        type=Path,
        help="Path to the action cases JSON file.",
    )
    parser.add_argument(
        "--case-id",
        help="Action case id for prepare-action or validate-action.",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        help="Workspace path for prepare-action or validate-action.",
    )
    parser.add_argument(
        "--top-k",
        default=3,
        type=int,
        help="Number of ranked skills to inspect for routing evals.",
    )

    args = parser.parse_args()

    if args.mode in {"prepare-action", "validate-action"}:
        if not args.case_id:
            parser.error("--case-id is required for action eval modes")
        if args.workspace is None:
            parser.error("--workspace is required for action eval modes")

    return args


def main() -> int:
    """Run the selected eval mode."""
    args = parse_args()

    if args.mode == "routing":
        failures = run_routing_eval(args.routing_cases, args.top_k)
        if failures:
            print(f"\n{failures} routing case(s) failed.")
            return 1

        print("\nAll routing cases passed.")
        return 0

    case = find_case(args.action_cases, args.case_id)

    if args.mode == "prepare-action":
        prepare_action_workspace(case, args.workspace)
        print(f"Prepared workspace: {args.workspace}")
        print(f"Prompt written to: {args.workspace / 'PROMPT.txt'}")
        return 0

    return validate_action_workspace(case, args.workspace)


if __name__ == "__main__":
    raise SystemExit(main())
