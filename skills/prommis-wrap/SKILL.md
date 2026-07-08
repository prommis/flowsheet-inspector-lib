---
name: prommis-wrap
description: Wraps a raw PrOMMiS/IDAES flowsheet with FlowsheetRunner and @FS.step decorators so it works with the Flowsheet Inspector VS Code extension. TRIGGER when: user says wrap, flowsheet missing decorators, FlowsheetRunner not set up, flowsheet not showing in VS Code, Flowsheet Inspector not picking up flowsheet, raw or unwrapped flowsheet. DO NOT TRIGGER when: flowsheet already wrapped, user wants to run or solve it, user wants to change a value or fix an import.
compatibility: Requires idaes-fi conda environment for flowsheets importing from prommis or idaes_fi, or prommis-dev for flowsheets importing from idaes_examples.
metadata:
  author: Tanushree Subramanian
  version: "1.0"
---

# PrOMMiS Flowsheet Wrapping

PrOMMiS flowsheets are Python simulations of minerals processing
plants built on the IDAES framework. The Flowsheet Inspector is
a VS Code extension that visualizes flowsheets, shows variable
values, and runs diagnostics — but only for wrapped flowsheets.

This skill wraps a raw flowsheet file with the decorators and
structure the Flowsheet Inspector needs.

## When to Use

Use this when:
- a flowsheet has no @FS.step decorators
- a flowsheet doesn't show up in the Flowsheet Inspector
- a flowsheet has no FlowsheetRunner setup
- you want to convert a raw flowsheet to work with the inspector

## Core Concepts

**FlowsheetRunner** — tracks each step, saves results to a database,
generates diagrams for the VS Code extension.

**@FS.step** — decorator placed above a function to label it as a
named step so the inspector knows about it. Step names must be valid
for the installed idaes-fi version — run `fi-steps --format text`
directly in the terminal to get the current list. Do not ask the
user to run it.

**Context** — shared object passed between steps so they can all
access the model, solver, and results.

**context.model** — where the flowsheet model lives inside context,
every step grabs it from here.

## Stage 1 — Understand the Flowsheet

Always announce: "Stage 1 — reading [filename]."

When the user names a file to wrap, read the file directly from
the workspace. Do not ask the user to paste it.

Determine and report:
- how many functions does it have
- does it have an initialize function
- does it have costing
- does it have an optimization objective
- which environment is needed based on its imports

Run `fi-steps --format text` directly in the terminal to get the
valid step names for the installed version before naming any steps
in the plan.

See references/wrapping-guide.md for the full decision tree on
which steps to include and how to name them.

## Stage 2 — Plan, Approve, Then Wrap

Always announce: "Stage 2 — wrapping plan."

Show the user a wrapping plan before touching anything. The plan
must list every item that needs to be shown and confirmed:
- every @FS.step function with its step name
- every plain helper function
- the steps= ordering tuple if needed
- the __main__ block

Count all items explicitly and state the total before asking for
confirmation. Verify the count matches the table before proceeding.

Once the plan is confirmed, immediately ask the user what to name
the wrapped file before writing anything:
"What would you like to name the wrapped file? Default is
[original_filename]_wrapped.py"

Wait for the user's response, then create that empty file in the
same folder as the original. All wrapped content goes into this
new file only. Never touch the original file.

If the flowsheet has more than 3 total plan items, wrap one item
at a time. After showing each item, ask for confirmation, then
write it directly to the new wrapped file before moving to the
next item.

If 3 or fewer total plan items, wrap everything, show the complete
result to the user, ask for confirmation, then write the file
directly.

While wrapping each @FS.step function, immediately check the step
name against fi-steps output before sending the response. Fix it
if it's not valid — do not wait until stage 3.

Once confirmed, announce: "Stage 2 — wrapping in progress."

See references/examples.md for a full example conversation and
the complete before/after flash flowsheet example.

## Stage 3 — Verify and Deliver

Always announce: "Stage 3 — running verification checklist."

DO NOT begin stage 3 until every single item in the plan has been
individually shown, confirmed, and written to the wrapped file.
Never claim a check passed for content that has not been written.

Run every check in references/quality-checklist.md and show each
one by name with its explicit pass or fail result — not a summary
claim like "all checks passed."

After all checks pass, confirm to the user that the wrapped file
is complete. Tell the user:
- the exact filename and folder it was saved to
- which conda environment to activate before running it
- the known _solver_out bug in idaes-fi 0.1.0

Do not output the whole file as a code block — it is already
written to disk.

## Related Skills

After wrapping, suggest these skills as next steps:
- `prommis-change-value` — to adjust operating conditions or
  parameter values in the wrapped flowsheet
- `prommis-explain-diagnostics` — if the flowsheet fails to solve
  or returns unexpected results
- `prommis-help-imports` — if any import paths are missing or wrong

## Output Rules

Never show the user:
- internal file reading operations
- fi-steps terminal command being run
- conda environment detection reasoning
- intermediate wrapping steps or internal checks
- step name validation reasoning
- any internal logic about which steps to include

Only show the user:
- the stage announcements
- the wrapping plan table
- each wrapped item one at a time with a confirmation question
- the verification checklist results by name with pass or fail
- the final filename and location after writing
- the conda environment to activate
- the known _solver_out bug note
- related skill suggestions

Keep all internal reasoning, terminal commands, file operations,
and environment detection invisible to the user. The user should
only see clean stage-by-stage output.

## Rules

- never change any flowsheet logic
- only add decorators, imports, and context handling
- always make a separate set_solver step
- never create a new SolverFactory inside solve steps
- always use tee=ctx["tee"] not tee=True
- never drop any lines from the original functions
- keep all original comments that still apply
- never use a step name not returned by fi-steps --format text
- always set explicit steps= ordering when flowsheet has both
  set_operating_conditions and initialize
- always write files directly — never ask the user to copy and paste
- always ask the user what to name the wrapped file before creating it
- ALWAYS create the wrapped file first before writing any content
  to it — ask for the filename right after the plan is confirmed
- NEVER edit the original file directly — all changes go to the
  new wrapped file only
- the original file must remain completely untouched throughout
  the entire wrapping process

## Common Pitfalls

See references/wrapping-guide.md for the full pitfalls list,
including the most critical ones: using an invalid step name,
forgetting steps= ordering, and claiming verification on unseen
content.

## Deviation Handling

If the user skips stage 1 and just names a file without context,
ask how many functions the flowsheet has and whether it has costing
or optimization steps before planning.

If a function was written incorrectly to the file, fix it directly
in the wrapped file and show the user only the corrected lines.
Never touch the original file.

## Reference Files

- references/wrapping-guide.md — step order, decision trees,
  how to get valid step names via fi-steps, naming rules,
  common pitfalls, file output instructions
- references/examples.md — full example conversation and
  before/after flash flowsheet example
- references/quality-checklist.md — verification steps,
  fallback instructions, tips for redirecting the AI