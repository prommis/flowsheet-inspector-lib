---
name: prommis-wrap
description: "Wraps a raw PrOMMiS/IDAES flowsheet with FlowsheetRunner and @FS.step decorators so it works with the Flowsheet Inspector VS Code extension. TRIGGER when: user says wrap, flowsheet missing decorators, FlowsheetRunner not set up, flowsheet not showing in VS Code, Flowsheet Inspector not picking up flowsheet, raw or unwrapped flowsheet. DO NOT TRIGGER when: flowsheet already wrapped, user wants to run or solve it, user wants to change a value or fix an import."
metadata:
  author: Tanushree Subramanian
  version: "1.1"
  compatibility: "Use prommis-dev for original flowsheets importing from idaes_examples; otherwise use idaes-fi for original flowsheets importing from prommis, idaes_fi, or idaes."
---

# PrOMMiS Flowsheet Wrapping

PrOMMiS flowsheets are Python simulations of minerals processing
plants built on the IDAES framework. The Flowsheet Inspector is
a VS Code extension that visualizes flowsheets, shows variable
values, and runs diagnostics but only for wrapped flowsheets.

This skill wraps a raw flowsheet file with the decorators and
structure the Flowsheet Inspector needs.

## Preserve Copied Code Formatting

When copying existing code from the original flowsheet into the wrapped file, preserve the copied code exactly except for the wrapper-required transformations listed below.

Do not change:
- import formatting
- line breaks
- blank lines
- comments
- spacing
- statement order
- internal indentation inside copied blocks

Permitted wrapper-required transformations are:
- adding `@FS.step(...)` decorators
- changing a step function signature to accept the selected `Context` variable
- adding access to the shared model, solver, results, and `tee` setting
- replacing `return m` with assignment to `context.model`
- replacing local solver creation and solve plumbing with the shared context
- adding the single outer indentation level required by a new wrapper function

Do not otherwise reformat, clean up, reorder, or alter copied code.

Add wrapper-only imports and wrapper-only code separately. Do not rewrite existing imports or copied flowsheet logic unless the user explicitly asks for that change.

## File Writing and Temporary Files

Write directly to the final wrapped `.py` file.

Do not create patch files, chunk files, helper scripts, or `.codex_*`
temporary files in the user's workspace in either one-shot mode or
function-by-function mode.

If temporary files are unavoidable, create them only in the system
temporary directory and delete them before responding.

The only new user-visible file should be the requested wrapped output
file.

## Core Concepts

**FlowsheetRunner**: tracks each step, saves results to a database,
generates diagrams for the VS Code extension. Its explicit `steps=`
sequence controls execution order; function-definition order and
decorator order do not.

**@FS.step**: decorator placed above a function to label it as a
named step so the inspector knows about it. Step names must be valid
for the installed idaes-fi version. Run `fi-steps --format text` in
the terminal to get the current list. If it is unavailable in the
current shell, run
`conda run -n <detected-environment> fi-steps --format text`.
Use the output only to validate names, not to choose execution order.
Do not ask the user to run either command.

**Context**: shared object passed between steps so they can all
access the model, solver, and results.

**context.model**: where the flowsheet model lives inside context,
every step grabs it from here.

## Stage 1: Understand the Flowsheet

Always announce: "Stage 1 reading [filename]."

When the user names a file to wrap, read the file directly from
the workspace. Do not ask the user to paste it.

Determine and report:
- how many functions does it have
- does it have an initialize function
- does it have costing
- does it have an optimization objective
- what execution sequence is used by `main()` or the equivalent
  entry point
- solver lifecycle: each creation or reconfiguration and its consuming solve
- which environment is needed based on the original flowsheet imports

Detect the environment before adding wrapper imports. Ignore the
wrapper-only `idaes_fi` import when choosing the environment.
Use these rules:
- if the original imports `idaes_examples`, use `prommis-dev`
- otherwise, if it imports `prommis`, `idaes_fi`, or plain `idaes`,
  use `idaes-fi`

Run `fi-steps --format text` in the terminal to get the valid step
names for the installed version before naming any steps in the plan.
If it is unavailable, run it through the detected conda environment.
Treat the result as a set of allowed names only.

Derive runtime order from the original `if __name__ == "__main__"`
block and the orchestration function it calls. If the entry point is
missing, dynamically dispatched, or ambiguous, stop and ask the user
to confirm the intended order instead of using the runner default.

See references/wrapping-guide.md for the full decision tree on
which steps to include, how to name them, and how to derive their
execution order.

## Stage 2: Plan, Approve, Then Wrap

Always announce: "Stage 2 wrapping plan."

Show the user a wrapping plan before touching anything. The plan
must list every item that will appear in the wrapped file:
- imports and runner setup with the derived execution order encoded
  in an explicit `steps=(...)` sequence
- every @FS.step function with its step name
- every plain helper function
- the __main__ block

Show the derived execution order immediately below the plan table as
plan information. Do not count it as a separate writable item because
the same order is already encoded in the runner-setup item.

If no valid step name accurately describes an original phase, choose
the closest valid name from the phase behavior. Show it as a
recommended compatibility mapping with one plain-language explanation
in the normal plan. Do not ask the user to design the mapping, and
never silently combine distinct phases.

Count all writable items explicitly and state the total before asking
for confirmation. Verify the count matches the table before proceeding.

With the plan, offer the user two wrapping modes:
1. Function-by-function mode: show and confirm each wrapped item before writing it. Recommend this for long or complex flowsheets.
2. One-shot mode: write the complete approved plan in one pass, then run the full quality checklist. Recommend this for short or simple flowsheets.

Ask the user to confirm the plan and select a mode. Do not select a
mode only from the file length.

Once the plan is confirmed and the mode is selected, immediately ask
the user what to name the wrapped file before writing anything:
"What would you like to name the wrapped file? Default is
[original_filename]_wrapped.py"

Wait for the user's response, then create that empty file in the
same folder as the original. All wrapped content goes into this
new file only. Never touch the original file.

In function-by-function mode, wrap one plan item at a time. Show the
item, ask for confirmation, write the confirmed item to the new file,
and only then move to the next item.

In one-shot mode, the approved plan is the content confirmation.
Write the complete wrapped file in one pass without asking for
item-by-item confirmations, then run the full verification checklist.

Always instantiate the runner with the exact approved order:
`FS = FlowsheetRunner(steps=(...))` or
`_FS = FlowsheetRunner(steps=(...))`. Keep `build` first, place the
wrapper-only `set_solver` at the original initial-solver setup
boundary before its consuming solve, and preserve the relative order
of all original model-processing phases. Never use bare
`FlowsheetRunner()` for a multi-step wrapped flowsheet.

While wrapping each @FS.step function, immediately check the step
name against fi-steps output before sending the response. Fix it
if it's not valid; do not wait until stage 3. Name validation must
not change the approved execution order.

Once the plan and mode are confirmed and the filename is known,
announce: "Stage 2 wrapping in progress."

See references/examples.md for a full example conversation and
the complete before/after flash flowsheet example.

## Stage 3: Verify and Deliver

Always announce: "Stage 3 running verification checklist."

Do not begin stage 3 until the selected mode's writing gate is met:
- function-by-function mode: every plan item has been individually
  shown, confirmed, and written
- one-shot mode: the approved plan has been written completely

Never claim a check passed for content that has not been written.

Run every check in references/quality-checklist.md and show each
one by name with its explicit pass or fail result not a summary
claim like "all checks passed."

The checklist must compare the wrapped runner sequence against the
execution order derived from the original entry point. Do not deliver
a wrapped file whose steps are valid but ordered differently.

After all checks pass, confirm to the user that the wrapped file
is complete. Tell the user:
- the exact filename and folder it was saved to
- which conda environment to activate before running it

Do not output the whole file as a code block it is already
written to disk.

## Related Skills

After wrapping, suggest these skills as next steps:
- `prommis-change-value` to adjust operating conditions or
  parameter values in the wrapped flowsheet
- `prommis-explain-diagnostics` if the flowsheet fails to solve
  or returns unexpected results
- `prommis-help-imports` if any import paths are missing or wrong

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
- the execution order derived from the original entry point
- in function-by-function mode, each wrapped item with a confirmation question
- in one-shot mode, no item-by-item content confirmation
- the verification checklist results by name with pass or fail
- the final filename and location after writing
- the conda environment to activate
- related skill suggestions

Keep all internal reasoning, terminal commands, file operations,
and environment detection invisible to the user. The user should
only see clean stage-by-stage output.

## Rules

- preserve copied-code formatting exactly except for the explicitly
  permitted wrapper transformations
- never run a formatter, auto-fixing linter, or import sorter on
  copied flowsheet code
- write directly to the final wrapped `.py` file; do not create
  patch files, chunk files, helper scripts, or `.codex_*` files in
  the user's workspace
- never change any flowsheet logic
- preserve the runtime order of the original entry point
- only add decorators, imports, and context handling
- always make a separate set_solver step for the initial solver
- place set_solver at the original initial-solver setup boundary
  before its consuming solve
- preserve every later solver creation or reconfiguration in the
  original phase before its consuming solve, storing the active solver
  in context
- preserve solver type, options, conditions, and solve arguments;
  never invent, remove, or consolidate solver configurations
- if the solver-to-solve mapping is ambiguous, recommend the best
  source-supported mapping with a plain-language reason in the plan
- if no valid step name accurately fits a phase, choose the closest
  valid name from its behavior and explain the recommended
  compatibility mapping in the normal plan; do not ask the user to
  design it or silently combine distinct phases
- always pass the approved mapped order explicitly to
  FlowsheetRunner(steps=(...))
- never use bare FlowsheetRunner() for a multi-step wrapped flowsheet
- never create a new SolverFactory inside solve steps
- always use `tee=<context-variable>["tee"]`, not `tee=True`
- never drop a copied source line except when making an explicitly
  permitted wrapper replacement
- keep all original comments that still apply
- never use a step name not returned by fi-steps --format text
- use fi-steps only to validate names, never to choose execution order
- always write files directly never ask the user to copy and paste
- always ask the user what to name the wrapped file before creating it
- ALWAYS create the wrapped file first before writing any content
  to it ask for the filename right after the plan is confirmed
- NEVER edit the original file directly all changes go to the
  new wrapped file only
- the original file must remain completely untouched throughout
  the entire wrapping process

## Common Pitfalls

See references/wrapping-guide.md for the full pitfalls list,
including the most critical ones: relying on the default runner
order, using an invalid step name, and claiming verification on
unseen content.

## Deviation Handling

If the user names a readable file without additional context, inspect
it directly and complete stage 1 from the file. Ask the user about its
functions, costing, or optimization only when the file cannot be read
or those details cannot be determined safely.

If the original entry point is missing or its execution order cannot
be determined safely, show the candidate mapped steps and ask the
user to confirm their intended order. Never substitute the order
printed by fi-steps or the bare FlowsheetRunner default.

If a function was written incorrectly to the file, fix it directly
in the wrapped file and show the user only the corrected lines.
Never touch the original file.

## Reference Files

- references/wrapping-guide.md execution-order derivation, decision trees,
  how to get valid step names via fi-steps, naming rules,
  common pitfalls, file output instructions
- references/examples.md full example conversation and
  before/after flash flowsheet example
- references/quality-checklist.md verification steps,
  fallback instructions, tips for redirecting the AI
