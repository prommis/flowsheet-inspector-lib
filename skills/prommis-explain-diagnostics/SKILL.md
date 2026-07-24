---
name: prommis-explain-diagnostics
description: "Run a named PrOMMiS, IDAES, WaterTAP, or Pyomo wrapped flowsheet, capture its IPOPT and IDAES DiagnosticsToolbox results, explain the important findings in plain language, and guide the user through one diagnostic or fix at a time. Use when a user asks to diagnose a flowsheet, investigate an IPOPT failure or infeasible solve, understand DiagnosticsToolbox warnings, or continue a diagnostic next step."
---

# PrOMMiS Explain Diagnostics

Run the flowsheet first, extract the useful solver and diagnostic evidence, and walk the user through one issue at a time in simple language. Keep commands, environment setup, and raw diagnostic detail internal.

## Core interaction

For a named flowsheet, use this user-facing sequence:

1. **Stage 1 — Running:** say which diagnostics skill is being used and that the flowsheet is running.
2. **Stage 2 — What happened:** say where the run stopped or whether it solved, explain that in one sentence, and show the highest-priority issue first.
3. **Stage 3 — Next step:** state the one action that needs attention and ask one clear question.
4. **After a change:** rerun the complete flowsheet, say whether the issue is fixed, and continue to the next issue only when needed.

Keep the explanation short. Show the main component, current value, allowed range, and source line when available. Summarize secondary warnings without letting them distract from the main issue.

Do not replace this loop with a source-gate rejection when a named flowsheet stops before IPOPT. Explain which phase stopped the run, use any retained model for structural and numerical diagnostics, and state clearly when no IPOPT result exists.

## Stage 1 run the flowsheet

Read `references/evidence-routing-guide.md` and `references/step-runner-guide.md`.

An explicit request to diagnose a named flowsheet authorizes one complete local, read-only run. Do not ask for permission again. Announce:

> Stage 1: running the flowsheet.
> I’m using the PrOMMiS diagnostics skill to run [filename] and explain what is stopping it.

Resolve a unique target and select a compatible installed Python interpreter from workspace and import evidence. Do not expose environment discovery unless it blocks the run.

Run the collector once in a fresh process:

```text
<selected-python> <skill-directory>/scripts/collect_diagnostics.py <flowsheet> --output <temporary-report>.json --quiet
```

The collector must execute the full registered sequence, capture solver output internally, retain partial model state after a failure, and run:

- `report_structural_issues()` whenever a model exists;
- `report_numerical_issues()` for a completed model;
- `display_variables_with_none_value_in_activated_constraints()` and `display_variables_at_or_outside_bounds()` for a partial model.

Use `diagnostics.evidence_scope` to distinguish a completed model from a partial model retained after a failed run.

Read the full JSON report, then remove the temporary file. Do not stop merely because a runner phase failed if diagnostic evidence or a partial model was retained.

For pasted IPOPT or DiagnosticsToolbox output, do not run a flowsheet merely to restate it. Interpret the pasted evidence and continue at Stage 2.

## Stage 2  explain the important results

Read `references/ipopt-guide.md` when a structured solver result or positively identified IPOPT log exists. Read `references/diagnostics-guide.md` for DiagnosticsToolbox output.

Announce:

> Stage 2 â€” here is what I found.

Use this user-facing format:

```text
Stage 2: what happened.

Solver output:
[exact EXIT line, or exact structured status and termination condition]
What this means: [one plain-English sentence]

Main issue:
[highest-priority component or WARNING line]
What this means: [one plain-English sentence]
Fix: [one short sentence describing the next action]
Source: [clickable flowsheet source line when available]

Other findings:
[one brief sentence summarizing lower-priority warnings]

[N] minor cautions â€” fix the warnings first.
```

For the main issue use exactly the labels `What this means:` and `Fix:`. Focus on variables, constraints, values, and code. Avoid chemistry explanations and unnecessary numerical-method terminology. Order findings using the priority in `references/diagnostics-guide.md`, not merely the order in which the reports printed them. Summarize secondary findings in one sentence unless the user asks for details.

Show only information needed for the next decision. Do not show IPOPT iteration tables, full model statistics, full tracebacks, constraint-violation dumps, environment discovery, or raw caution details unless the user asks.

If no IPOPT result exists, say:

```text
Solver output:
No IPOPT result was produced because the flowsheet stopped during [phase or step].
What this means: The run did not reach the main solve.
```

Then explain the available DiagnosticsToolbox warnings from the retained model. Label partial-model evidence clearly. Do not present partial structural warnings as the original root cause without confirming evidence.

When the numerical report or partial-model bounds check identifies a fixed variable outside its bounds, prioritize that explicit value-and-bounds finding over missing-value output, structural artifacts, or potential evaluation errors. Inspect the flowsheet source for the matching specification.

## Stage 3 one next step

If the collected evidence already identifies a component and current violation, do not ask to run another diagnostic method. Inspect the matching source specification and continue to the fix question.

Announce:

> Stage 3 â€” next step.

Prefer the exact method named by the installed DiagnosticsToolbox report. If multiple methods are listed, apply the priority in `references/diagnostics-guide.md` and choose the method most likely to identify the component behind the highest-priority warning. Verify the exact method on the installed object and inspect its signature before suggesting it.

When more diagnostic detail is needed, ask in this format and then stop:

```text
I need to identify [plain-English target].
Can I run dt.<method>() to [one short plain-English description]?
```

Do not run multiple follow-ups or present a menu.

If the user agrees, run the collector in a fresh process with the exact method:

```text
<selected-python> <collector> <flowsheet> --follow-up <method> --output <temporary-report>.json --quiet
```

Show only relevant component lines using the same three-line explanation style. If the method was not suggested by the current report, is unavailable, or requires unsupported arguments, do not substitute a fuzzy match; explain the limitation.

## Fix and verification loop

Propose a change only after the evidence identifies a component and an expected improvement. Offer:

```text
Want me to fix this, or will you do it?
- If I fix it: I will make the change and re-check.
- If you fix it: make the change and tell me when it is ready; I will inspect and re-check it.
```

Do not invent a replacement value. For a fixed value outside its bounds, show the current value, allowed range, and matching flowsheet specification, then ask the user how they want to correct it.

When a value must be supplied, ask one combined question: what value should replace the invalid value, and should Codex make the change and rerun or will the user change it?

Only edit files the user placed in scope. Never edit installed IDAES, Pyomo, IPOPT, property-package, or runner source as a flowsheet fix unless the user explicitly expands scope.

After any approved change:

1. Announce `Re-checking the flowsheet after the change...`.
2. Preserve unrelated edits.
3. Run the complete flowsheet again in a fresh process.
4. Say whether the original issue is fixed.
5. Compare solver termination, structural warnings, numerical warnings, and the original component finding.
6. Continue to the next issue only when needed. Do not make another change silently.

## Stopping conditions

Stop and summarize when:

- IPOPT reports a successful termination and DiagnosticsToolbox has no warnings;
- all warnings are resolved and only cautions remain;
- the next change is outside the authorized flowsheet scope;
- the same warning remains after two verified fix attempts and the user does not want deeper investigation;
- the user asks to stop.

Do not chase cautions automatically.

## Resources

- `references/evidence-routing-guide.md`: distinguish full-run evidence, partial-run evidence, and pasted output.
- `references/ipopt-guide.md`: translate common IPOPT results and choose the next diagnostic check.
- `references/diagnostics-guide.md`: translate DiagnosticsToolbox warnings and map them to focused methods.
- `references/step-runner-guide.md`: collector execution, presentation contract, fix loop, and final summaries.
- `scripts/collect_diagnostics.py`: deterministic full-run evidence collector and focused follow-up runner.
