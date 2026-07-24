# Full-Run and Fix Guide

Use this guide for named flowsheets, focused follow-ups, and before/after verification.

## Run the complete flowsheet

A named-flow diagnosis authorizes one complete, local, read-only run. Announce Stage 1, name the diagnostics skill, say which flowsheet is running, and proceed without another permission question. Hide commands and environment setup.

Resolve the target and compatible interpreter, then run:

```text
<python> <skill>/scripts/collect_diagnostics.py <flowsheet> --output <temporary>.json --quiet
```

The collector:

- imports the target by path;
- discovers a unique public runner;
- executes every registered step in order;
- captures console output, including solver output;
- retains the public model and solver result after success or failure;
- runs structural diagnostics whenever a model exists;
- runs the full numerical report for a completed model;
- runs the safe missing-value and bounds checks for a partial model;
- labels diagnostics as completed-model or partial-model evidence.

Remove the temporary JSON after reading it. Do not repeat the same full run merely to collect the same evidence.

## Present results

Show this sequence:

```text
Stage 2 â€” here is what I found.

Solver output:
[exact EXIT line or structured result]
What this means: [one sentence]

Main issue:
Evidence scope: [completed model or partial model after a failed run]
[highest-priority component or WARNING]
What this means: [one sentence]
Fix: [one sentence]
Source: [clickable flowsheet source line when available]

Other findings:
[one sentence summarizing lower-priority warnings]

[N] minor cautions â€” fix the warnings first.

Stage 3 â€” next step.
[Only when the cause is still unclear:]
I need to identify [plain-English target].
Can I run dt.<method>() to [plain-English purpose]?
```

If the evidence already identifies a component and current violation, omit the Stage 3 method question. Inspect the matching source specification and continue to the fix question.

If more diagnosis is needed, stop after the Stage 3 method question. Do not run the follow-up until the user answers.

Apply the priority in `diagnostics-guide.md`. Show an explicit current bounds violation before broad structural or potential warnings from a partial model.

Do not show full IPOPT iteration tables, model-statistics blocks, complete tracebacks, environment selection, or raw caution details unless requested.

## Run an approved focused method

The method must be named by the current DiagnosticsToolbox report and callable on the installed object. Run it against a fresh reproduction of the same model state:

```text
<python> <collector> <flowsheet> --follow-up <exact-method> --output <temporary>.json --quiet
```

Read the `diagnostics.follow_up` record and show only the component lines relevant to the warning. If the fresh run is not comparable, say why. Do not rerun for another focused method without the user's approval.

## Propose one fix

Do not propose a change until a component, source location, and expected improvement are supported. Inspect the matching flowsheet source before asking about a fix.

State the one action that needs attention and ask one clear question:

```text
Stage 3: next step.
[one sentence describing the action]
[one clear question asking for the needed decision and who should make the change]
```

For a fixed value outside its bounds, show the current value, allowed range, and matching `.fix()` specification. Do not guess a replacement value. Ask what value should replace it and whether Codex should make the change and rerun or the user will change it.

Examples of in-scope flowsheet fixes:

- correcting an invalid `.fix()` value;
- adding or removing a specification to correct DOF;
- deactivating a confirmed redundant constraint;
- adding or correcting flowsheet-level scaling;
- correcting units in the provided flowsheet.

Do not edit installed package or runner internals as a flowsheet fix. Identify out-of-scope property-package or library code and explain what the evidence shows.

## Verify

After an approved edit:

1. Announce `Re-checking the flowsheet after the change...`.
2. Inspect the current file and preserve unrelated changes.
3. Rerun the complete collector in a fresh process.
4. Say whether the original issue is fixed.
5. Compare the same solver and diagnostic categories.
6. Walk the user to the next issue only if needed.

If the user edits the file, inspect it directly rather than asking them to paste output.

## Stop and summarize

Stop when:

- the solver succeeds and no DiagnosticsToolbox warnings remain;
- only cautions remain;
- the needed change is outside scope;
- the same warning remains after two verified fix attempts and the user chooses to stop;
- the user asks to stop.

Successful summary:

```text
All done. Your flowsheet solved successfully and DiagnosticsToolbox found no warnings.
```

Fixed summary:

```text
All done. I fixed [issue]. The rerun changed from [before] to [after], and the original warning is gone.
```

Unresolved summary:

```text
The flowsheet still stops at [phase/result]. The remaining issue is [plain-English finding]. The next useful check is [one action].
```
