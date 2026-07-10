# PrOMMiS Skill Evals

This folder contains evals for the PrOMMiS agent skills in `skills/`.

The first eval layer checks routing: given a plain-English user request,
`skill-search` should rank the expected PrOMMiS skill first.

Run the routing eval from the repository root:

```bash
python evals/prommis-skills/run_eval.py
```

Current evals:

- `cases/routing_cases.json`: plain-English prompts with expected skill names
- `cases/action_cases.json`: file-action cases with fixtures and validators
- `fixtures/`: sample workspaces copied before action evals
- `validators/`: scripts that check action eval outputs

## Action Evals

Action evals use a fixture workspace, a user prompt, and a validator.

Prepare a fresh workspace for an action eval:

```bash
python evals/prommis-skills/run_eval.py ^
  --mode prepare-action ^
  --case-id wrap_methanol_flowsheet ^
  --workspace C:\tmp\prommis-wrap-eval
```

Then run an agent in that workspace using the prompt in `PROMPT.txt`.

After the agent creates the expected output file, validate it:

```bash
python evals/prommis-skills/run_eval.py ^
  --mode validate-action ^
  --case-id wrap_methanol_flowsheet ^
  --workspace C:\tmp\prommis-wrap-eval
```

Later layers can add agent runners for Codex, Claude Code, Gemini, or other
agents so the action evals can run end to end.
