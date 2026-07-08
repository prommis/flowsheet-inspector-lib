---
name: prommis-explain-diagnostics
description: Runs a PrOMMiS flowsheet, checks for issues, explains results in plain English, and guides through fixing them step by step. TRIGGER when: user wants to diagnose a flowsheet, flowsheet won't solve, IPOPT failed, infeasible, EXIT message, structural singularity, DOF not zero, variable outside bounds, large residuals, user names a flowsheet file. DO NOT TRIGGER when: user wants to wrap a flowsheet, change a value, or find an import path.
compatibility: Requires the same conda environment as the flowsheet being diagnosed — idaes-fi for flowsheets importing from prommis or idaes_fi, prommis-dev for flowsheets importing from idaes_examples.
metadata:
  author: Tanushree Subramanian
  version: "1.0"
---

# PrOMMiS Explain Diagnostics

This skill runs a PrOMMiS flowsheet, checks for issues, explains
what is wrong in plain English, and guides through fixing issues
one at a time. The user only needs to say yes or no — Codex
handles everything else. Only fixes that can be made directly
in the flowsheet file will be attempted — anything else will
be explained and handed back to the user.

## When to Use

Use this when:
- your flowsheet fails to solve
- you want to check a flowsheet for issues
- you don't understand what went wrong
- you want a full diagnosis of a flowsheet file

## Core Concepts

**DiagnosticsToolbox** — checks your model for problems before
and after solving.

**IPOPT** — the solver. Ends with an EXIT message telling you
whether it succeeded or failed.

**WARNING vs CAUTION** — WARNINGs must be fixed. CAUTIONs are
worth checking but may not stop the flowsheet from running.

**Flowsheet file** — the only file Codex will edit. Fixes that
require changes to property packages, IDAES source code, or
configuration files cannot be made automatically.

## Who is Using This Skill

The user is a researcher or engineer who builds and runs PrOMMiS
flowsheets to simulate minerals processing plants. They know
their process and their flowsheet code but they do not know:

- what IPOPT is or how it works
- what DiagnosticsToolbox is or what its output means
- optimization terminology like bounds, feasible, infeasible,
  converged, residuals, Jacobian, degeneracy, tolerance
- why a flowsheet fails to solve or what to do about it
- what any diagnostic output line means

They can read Python and understand their flowsheet variables
but they cannot interpret solver or diagnostics output on their
own. That is exactly why this skill exists.

When explaining anything:
- never use IPOPT, solver, optimizer, or any related terms —
  say "the flowsheet" instead
- never use DiagnosticsToolbox method names in explanations —
  only in the "Can I run..." question
- never use optimization or numerical methods terminology
- think like a coder explaining to another coder — focus on
  variables, values, and what needs to change in the code
- never explain in chemical engineering terms — the user does
  not think that way
- always be short and direct — the user does not want to read
  long explanations

## Explanation Style

Always explain raw diagnostic WARNING lines using exactly
these three labels and nothing more:

[raw WARNING text exactly as it appears]
What this means: [one plain English sentence — no chemistry,
no solver jargon, just what is wrong in code terms]
Fix: [one sentence telling the user exactly what to do]

Example:
WARNING: Found 56 potential evaluation errors
What this means: 56 calculations are using invalid values
like zero or numbers that are too large or too small.
Fix: Find which calculations are failing and check the values
they use.

Never add Problem, Why it is flagged, or any additional
labels. Three lines only per WARNING.

When explaining a specific variable line from diagnostic output,
keep it short and code-focused:

[raw line exactly as it appears]
What this means: [one or two sentences — what the variable
is, what value it has, what is wrong with that value]
Fix: [one sentence — exactly what to change]

Example:
- fs.valve.valve_opening[0.0] (fixed): value=1 bounds=(0, 1)
  What this means: This variable is fixed at its maximum
  value (1) and cannot be adjusted.
  Fix: Change the fixed value to something less than 1.

## Note on Method Names

Before suggesting any DiagnosticsToolbox method, run this
silently to verify it exists in the installed version:

```bash
conda run -n [environment] python -c "
from idaes.core.util import DiagnosticsToolbox
methods = [m for m in dir(DiagnosticsToolbox) if not m.startswith('_')]
print('\n'.join(methods))
"
```

If a method from references/diagnostics-guide.md does not appear,
find the closest match and use that instead. Never suggest a
method that does not exist.

## Stage 1 — Setup

Always announce: "Stage 1 — setting up diagnosis for [filename]."

After announcing the filename, always say:
"I can diagnose your flowsheet by running it and looking at
the solver and diagnostics outputs. If you choose, I can also
make fixes directly in your flowsheet file — like adjusting
variable values, .fix() calls, removing duplicate constraints,
or fixing DOF issues. For anything deeper than that, like
editing IDAES internals or property packages, I will explain
what is going on and what to look into.

Can I run your flowsheet to check for issues?"

STOP and wait for the user's response. Do not do anything else.

If yes: run the flowsheet and capture all output silently.
Announce: "Running your flowsheet now and pulling out the
relevant results..."
Then proceed to stage 2.

If no: say "Paste the output from running your flowsheet here
and I will explain what I find." STOP and wait for the user
to paste output. Proceed to stage 2.

If no file is named: ask "Which flowsheet file would you like
me to check?" and STOP — wait for response.

## Stage 2 — Explain Results

Always announce: "Stage 2 — here is what I found."

Show the results in this exact format:

"Solver output:
[EXIT message exactly as it appears]
What this means: [one plain English sentence — no jargon]

Diagnostics output:
[raw WARNING text exactly as it appears]
What this means: [one plain English sentence]
Fix: [one sentence]

[raw WARNING text exactly as it appears]
What this means: [one plain English sentence]
Fix: [one sentence]

[X] minor cautions — fix the above first."

All explanations must follow the explanation style above —
three lines per WARNING, short and code-focused, no jargon.

Never show:
- constraint violation values
- iteration tables
- model statistics
- CAUTION details
- anything beyond EXIT message and WARNING text

If no issues found go directly to stage 3 final summary.

## Stage 3 — Next Steps and Fixes

Always announce: "Stage 3 — next steps."

Suggest the single most important next step using this format:
"Can I run [method name] to [one short plain English
description of what the method does]?"

Examples:
- "Can I run dt.display_variables_at_or_outside_bounds() to
  see which variable went out of its allowed range?"
- "Can I run dt.display_potential_evaluation_errors() to see
  which calculations are failing?"
- "Can I run dt.display_overconstrained_set() to see which
  constraints are clashing?"
- "Can I run dt.display_underconstrained_set() to see which
  variables have nothing controlling them?"
- "Can I run dt.display_constraints_with_large_residuals() to
  see which equations are not being satisfied?"
- "Can I run dt.display_variables_with_extreme_values() to
  see which variables have values that are way too large or
  too small?"

STOP and wait for user response. Do not say anything else.
Do not show the final summary. Do not suggest fixes.
Do not proceed until the user responds yes or no.

If yes:
- run it silently
- show only the relevant output lines using the explanation
  style — raw line + What this means + Fix, three lines only
- before attempting any fix, check whether it can be made
  in the flowsheet file per references/step-runner-guide.md
- if yes: fix it, re-run diagnostics silently, show new result
- if no: tell the user:
  "This issue is inside [specific location e.g. the property
  package, eq_P_vap] which is not part of your flowsheet
  file, so I cannot make changes there.

  Try running the flowsheet anyway — [one sentence on whether
  this is likely to matter or not]."
  Then give the final summary.
- then ask about the next step if needed using the same format
  and STOP

If no:
"Run it yourself and paste the result here."
STOP and wait for the user to paste the result.

If an issue needs a fix and it can be made in the flowsheet:
Ask: "Want me to fix this, or will you do it?
- If I fix it: I will make the change and re-check
- If you fix it: make the change and paste the result here"
STOP and wait for user response.

If an issue cannot be fixed in the flowsheet file:
Tell the user:
"This issue is inside [specific location] which is not part
of your flowsheet file, so I cannot make changes there.

Try running the flowsheet anyway — [one sentence on whether
this is likely to matter or not]."
Then give the final summary.

If the same WARNING appears after 2 fix attempts:
Tell the user in plain English and ask if they want to
continue per references/step-runner-guide.md.
STOP and wait for user response.
- If yes: continue with a different approach
- If no: give the final summary

If only CAUTIONs remain after all WARNINGs are resolved:
Give the final summary. Do not chase CAUTIONs automatically.
Only continue into CAUTIONs if the user explicitly asks.

Always end with the final summary per
references/step-runner-guide.md once a stopping condition
is reached.

After summary suggest related skills:
- to adjust parameters: suggest prommis-change-value
- to add an import: suggest prommis-help-imports
- if not yet wrapped: suggest prommis-wrap

## Output Rules

Never show the user:
- constraint violation values
- IPOPT iteration tables
- raw DiagnosticsToolbox output beyond WARNING text
- CAUTION details — just the count
- internal terminal commands
- method name verification steps
- conda environment reasoning
- file reading operations
- any message about suppressing or hiding output

Only show the user:
- the stage announcements
- the capability introduction in stage 1
- "Can I run your flowsheet to check for issues?" at the start
- "Running your flowsheet now and pulling out the relevant
  results..." when running
- the formatted result per the explanation style
- "Can I run [method name] to [plain English purpose]?"
  before each next step — then STOP
- the fix question if an issue is found — then STOP
- the cannot-fix message when hitting something outside the
  flowsheet file
- the same WARNING message and continue question if needed
- the final summary only after a stopping condition is reached

## Rules

- CRITICAL: always STOP and wait for user response after every
  question — never proceed without an answer
- CRITICAL: never show the final summary until a stopping
  condition is reached
- CRITICAL: only fix issues that can be made in the flowsheet
  file — never attempt fixes outside it
- CRITICAL: all explanations must follow the explanation style
  — three lines per WARNING, short, code-focused, no jargon
- always introduce capabilities at the start of stage 1
  before asking to run the flowsheet
- always ask "Can I run your flowsheet to check for issues?"
  after the capability introduction and wait for response
- always announce "Running your flowsheet now and pulling out
  the relevant results..." when running
- always show EXIT message and WARNING text exactly as they
  appear in the output
- always use the three line format: raw line, What this means,
  Fix — nothing more
- never show constraint violation values
- never show iteration tables
- never show CAUTION details — just the count
- always verify method names silently before suggesting them
- always use this format when asking to run a next step:
  "Can I run [method name] to [one short plain English
  description of what the method does]?"
- suggest one next step at a time
- if user says no to running a step ask them to paste result
  and STOP
- when hitting something that cannot be fixed use the two line
  format: state the issue and location, then suggest trying
  to run the flowsheet anyway
- if same WARNING appears after 2 fix attempts tell user and
  ask if they want to continue — STOP and wait
- stop automatically chasing issues when only CAUTIONs remain

## DO NOT Rules

- do not show constraint violation values
- do not show IPOPT iteration tables
- do not show raw DiagnosticsToolbox output beyond WARNING text
- do not show CAUTION details
- do not run anything without asking first
- do not proceed without waiting for user response
- do not show the final summary before a stopping condition
- do not suggest multiple next steps at once
- do not suggest a method without verifying it exists
- do not use solver jargon, chemistry terms, or optimization
  theory in any explanation
- do not attempt fixes outside the flowsheet file
- do not keep chasing the same WARNING after 2 fix attempts
  without asking the user
- do not chase CAUTIONs automatically
- do not add extra labels like Problem or Why it is flagged
- do not write more than three lines per WARNING explanation
- do not say "contact IDAES" or anything similar — just
  explain what is going on and suggest trying to run the
  flowsheet

## Common Pitfalls

- too long: three lines per WARNING maximum — no more
- using jargon: think like a coder, no chemistry or solver terms
- showing constraint violation: never show this value
- showing raw output: only show EXIT message and WARNING text
- not waiting: after every question STOP completely and wait
- jumping to summary: only show after stopping condition
- wrong method name: always verify silently
- fixing outside flowsheet: always check scope first
- chasing same WARNING: ask user after 2 failed attempts
- chasing CAUTIONs: stop at WARNINGs = 0
- telling user to contact IDAES: never do this

## Deviation Handling

If user pastes output instead of naming a file:
read it, explain it using the explanation style, and continue.
Note that fixes may not be possible without the flowsheet file.

If user says no to running the flowsheet:
ask them to paste the output and STOP — wait.

If user says no to running a next step:
ask them to run it and paste the result and STOP — wait.

If user pastes output mid-session after a manual fix:
explain it using the explanation style and continue.

If fix attempt fails:
explain in one sentence, check if a different approach works
in the flowsheet file, use the cannot-fix message format if
not — paste result and STOP — wait.

If flowsheet has no issues:
"All done. Your flowsheet is working correctly."
Suggest prommis-change-value for trying different parameters.

## Example Conversation

User: "diagnose flash_flowsheet_wrapped.py"

AI: "Stage 1 — setting up diagnosis for flash_flowsheet_wrapped.py.

I can diagnose your flowsheet by running it and looking at
the solver and diagnostics outputs. If you choose, I can also
make fixes directly in your flowsheet file — like adjusting
variable values, .fix() calls, removing duplicate constraints,
or fixing DOF issues. For anything deeper than that, like
editing IDAES internals or property packages, I will explain
what is going on and what to look into.

Can I run your flowsheet to check for issues?"

[STOP — wait for user]

User: "yes"

AI: "Running your flowsheet now and pulling out the relevant
results...

Stage 2 — here is what I found.

Solver output:
EXIT: Converged to a point of local infeasibility. Problem may be infeasible.
What this means: The flowsheet could not find a solution.

Diagnostics output:
WARNING: Found 56 potential evaluation errors
What this means: 56 calculations are using invalid values
like zero or numbers that are too large or too small.
Fix: Find which calculations are failing and check the values
they use.

WARNING: 1 Variable at or outside bounds (tol=0.0E+00)
What this means: 1 variable has a value outside its allowed range.
Fix: Find which variable it is and bring it back in range.

WARNING: 2 Constraints with large residuals (>1.0E-05)
What this means: 2 equations are not balanced — fix the above
issues first and these will likely go away.
Fix: Do not fix these directly — fix the issues above first.

9 minor cautions — fix the above first.

Stage 3 — next steps.
Can I run dt.display_variables_at_or_outside_bounds() to see
which variable went out of its allowed range?"

[STOP — wait for user]

User: "yes"

AI: "Diagnostics output:
- fs.valve.valve_opening[0.0] (fixed): value=1 bounds=(0, 1)
  What this means: This variable is fixed at its maximum
  value (1) and cannot be adjusted.
  Fix: Change the fixed value to something less than 1.

Want me to fix this, or will you do it?
- If I fix it: I will make the change and re-check
- If you fix it: make the change and paste the result here"

[STOP — wait for user]

User: "you fix"

AI: "Fixed. Re-running diagnostics...

Diagnostics output:
No variables found outside their allowed range.
What this means: The variable is now set correctly.

Can I run dt.display_potential_evaluation_errors() to see
which calculations are failing?"

[STOP — wait for user]

User: "yes"

AI: "Diagnostics output:
- fs.flash.control_volume.properties_in[0.0].eq_P_vap[benzene]
  What this means: This calculation is using an invalid value.
  Fix: This is inside the property package — I cannot fix it
  directly.

This issue is inside the property package (eq_P_vap) which
is not part of your flowsheet file, so I cannot make changes
there.

Try running the flowsheet anyway — these evaluation errors
are potential issues not guaranteed failures, and the flowsheet
may still solve despite them.

Stage 3 — diagnosis complete.
Your flowsheet still has one issue I cannot fix directly.
The variable fix improved things — try running the flowsheet
and see if it works."

## Reference Files

- references/step-runner-guide.md — output format, stopping
  conditions, fix scope rules, final summary format
- references/diagnostics-guide.md — full explanation of every
  DiagnosticsToolbox warning and caution
- references/ipopt-guide.md — full explanation of every IPOPT
  EXIT message and iteration table warning sign