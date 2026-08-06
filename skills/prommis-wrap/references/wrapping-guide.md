# Wrapping Reference Guide

## Contents

- [Plan and approval](#step-0--plan-then-approve)
- [Protect the original file](#critical--never-edit-the-original-file)
- [Validate step names](#critical--valid-step-names-are-not-execution-order)
- [Derive execution order](#critical--derive-execution-order-from-the-original-entrypoint)
- [Step purposes](#what-each-step-does)
- [Solver lifecycle](#preserve-solver-lifecycle)
- [Step-selection decision tree](#decision-tree--which-steps-to-include)
- [Wrapping modes](#wrapping-mode-procedures)
- [Step naming](#how-to-name-each-step)
- [Runner and context names](#runner-variable-name)
- [Substeps](#substeps)
- [Wrapping rules](#wrapping-rules)
- [Common pitfalls](#common-pitfalls)
- [File output](#file-output)
- [References and examples](#reference)

## Step 0 — Plan Then Approve

Before wrapping anything, show the user a plan. The plan must list
every single piece of the final file, not just the `@FS.step`
decorated functions. This includes:

- the imports and wrapper setup (`FlowsheetRunner`, `Context`, and the
  derived execution order encoded in an explicit
  `FlowsheetRunner(steps=(...))` sequence)
- every function getting a @FS.step decorator
- every plain helper function that stays undecorated (e.g. report)
- the final `__main__` block with the selected runner's `run_steps()`

Show the derived execution order immediately below the plan as plan
information. Do not count it as a separate writable item because it
is already encoded in the runner-setup item.

When moving code into `@FS.step` functions, follow the copied-code
formatting rule in `SKILL.md`. Preserve copied code exactly except
for the explicitly permitted wrapper transformations.

With the plan, offer two wrapping modes:
1. Function-by-function mode: show, confirm, and write each plan item individually.
2. One-shot mode: write the complete approved plan in one pass, then run the quality checklist without item-by-item confirmations.

Ask the user to confirm the plan and select a mode. Use the selected
mode throughout stages 2 and 3.

After listing all plan items, count them explicitly and state the
total: "Total plan items: X". Then verify that
count matches the actual number of rows in the plan table before
asking for confirmation. If the count is wrong, correct it before
proceeding — a wrong count at stage 2 will cause a false-complete
signal at stage 3.

Example:
"I found 4 functions in flash_flowsheet.py. Here is my wrapping plan:
- imports and wrapper setup -> add FlowsheetRunner, Context, and an
  explicit steps sequence
- build_model -> @FS.step("build")
- set_operating_conditions -> @FS.step("set_operating_conditions")
- init_model -> @FS.step("initialize")
- solve -> @FS.step("solve_initial")
- adding new set_solver step
- __main__ block -> replaced with FS.run_steps()
Execution order: build, set_operating_conditions, initialize,
set_solver, solve_initial
Total plan items: 7
Confirm this plan and choose function-by-function or one-shot mode."

If the flowsheet has a plain helper function like report(m) that is
called from steps but not itself decorated, list it explicitly:
"- report(m) -> stays as plain helper, no decorator, shown unchanged
  in the wrapped file"

Wait for plan confirmation and mode selection before wrapping.

After plan confirmation and mode selection, immediately ask the user
what to name the wrapped file before writing anything:
"What would you like to name the wrapped file? Default is
[original_filename]_wrapped.py"

Create that empty file in the same folder as the original. All
wrapped content goes into this new file only. Never touch the
original file at any point during the wrapping process.

## CRITICAL — Never Edit the Original File

All wrapping changes go into the new wrapped file only. The original
file must remain completely untouched throughout the entire wrapping
process. If a mistake is made, fix it in the wrapped file — never
in the original.

## CRITICAL — Valid Step Names Are Not Execution Order

The valid step names are defined by the installed version of idaes-fi.
Run this directly in the terminal to get the current list:

```bash
fi-steps --format text
```

If that command is unavailable in the current shell, run:

```bash
conda run -n <detected-environment> fi-steps --format text
```

Run this yourself — do not ask the user to run it. Treat the output
strictly as the set of valid names for the installed version. Do not
copy its displayed order into the wrapped flowsheet. The correct
execution order comes from the original flowsheet's entry point and
may differ from the order printed by `fi-steps`.

Documentation: docs/usage.md in the flowsheet-inspector-lib repo.

If no valid name accurately describes a phase, choose the closest
valid name from its behavior. Show it as a recommended compatibility
mapping with one plain-language explanation in the normal plan. Do not
ask the user to design the mapping, and never silently combine phases.

## CRITICAL — Derive Execution Order from the Original Entrypoint

A bare `FlowsheetRunner()` uses the installed library's default step
order. Function-definition order and decorator order do not override
that default. Never assume the default order is correct for the
flowsheet being wrapped.

Before writing the wrapping plan:

1. Locate the original `if __name__ == "__main__"` block.
2. Follow its call into `main()` or the equivalent orchestration
   function and read that function completely.
3. Record each flowsheet phase in the order it actually executes,
   including function calls and inline solve, costing, or optimization
   sections.
4. Map each phase to a valid step name returned by `fi-steps`.
5. Preserve the relative order of all original model-processing phases.
6. Keep `build` first. Represent the original initial solver setup as
   `set_solver` at the same runtime boundary before its consuming solve.
7. Exclude plain helpers from the runner sequence and include every
   decorated step exactly once.
8. Show the mapped sequence in the wrapping plan and use that exact
   sequence in `FlowsheetRunner(steps=(...))`.

For example, if the original entry point executes build, operating
conditions, scaling, initialization, and solve in that order, write:

```python
FS = FlowsheetRunner(
    steps=(
        "build",
        "set_solver",
        "set_operating_conditions",
        "set_scaling",
        "initialize",
        "solve_initial",
    )
)
```

Do not use bare `FS = FlowsheetRunner()` for a multi-step wrapped
flowsheet. If the original has no entry point, uses dynamic dispatch,
or has an ambiguous execution order, show the best source-supported
order with one plain-language reason in the plan. Do not ask the user
to design the order or silently use the installed default.

If multiple original functions logically belong to the same valid
step name and duplicate decorated names are unsupported, do not give
one function a misleading name merely to make it unique. Keep the
original functions as plain helpers and create one wrapper-only
decorated adapter that calls them in their original runtime order.
Show that adapter as the recommended handling in the normal plan with
a plain-language reason.

## What Each Step Does

build — creates ConcreteModel, FlowsheetBlock, and all unit models.
Stores the model in the selected context variable at the end. Never
returns m.

set_solver — creates the initial solver and stores it in the selected
context variable. Later original solver changes follow the solver
lifecycle rule below.

set_operating_conditions — fixes all input variables with .fix() calls.
This is where parameter changes happen.

initialize — initializes unit models before solving. Not always present.

set_scaling — sets manual scaling factors on variables and constraints.

solve_initial — solves the flowsheet at fixed operating conditions.
Always uses the selected context variable for the solver and `tee`.

set_autoscaling — applies automatic scaling after the initial solve.

add_costing — adds costing blocks to the flowsheet.

initialize_costing — initializes costing blocks. Do not use this name
for an unrelated second solve solely to obtain a unique step name;
use the duplicate-purpose adapter guidance above.

setup_optimization — unfixes variables and adds an objective function.

solve_optimization — solves the optimization problem.

## Preserve Solver Lifecycle

Trace each original solver creation or reconfiguration to the solve
that consumes it. Use `set_solver` for the initial setup at its
original boundary; keep later changes in their original phase and
store the active solver in context. Preserve solver type, options,
conditions, and solve arguments. Never invent, remove, consolidate,
or reorder configurations. If the mapping is ambiguous, recommend the
best source-supported mapping with a plain-language reason in the plan.

## Decision Tree — Which Steps to Include

Does the flowsheet have an initialize function?
- Yes -> wrap it as @FS.step("initialize").

Does the flowsheet have costing?
- Yes -> include add_costing and initialize_costing
- No -> skip those steps

Does the flowsheet have an optimization objective?
- Yes -> include setup_optimization and solve_optimization
- No -> do not add them automatically; show a recommended compatibility
  mapping if a distinct phase has no accurate valid name

Is it a simple simulation?
- Yes -> include only the steps present in the original and preserve
  their entry-point order, placing `set_solver` at the original
  initial-solver boundary.

Does the flowsheet have plain helper functions called from inside
steps (e.g. report(m))?
- Yes -> include them as items in the plan and keep them unchanged.
  Confirm them individually only in function-by-function mode.

## Wrapping Mode Procedures

Count all plan items regardless of mode. File length may inform the
recommendation, but the user selects the mode.

### Function-by-Function Mode

- create the empty named wrapped file after plan approval
- handle exactly one plan item at a time
- validate a decorated step name before showing the item
- show the item and ask for confirmation
- write only the confirmed item to the wrapped file
- continue until every plan item is confirmed and written
- run the complete quality checklist

### One-Shot Mode

- create the empty named wrapped file after plan approval
- treat the approved plan as the content confirmation
- validate every decorated step name before writing
- write every plan item to the wrapped file in one pass
- do not request item-by-item confirmations
- run the complete quality checklist against the written file

In both modes, never touch the original file and never begin Stage 3
until the mode's complete writing gate has been met.

## How to Name Each Step

Run `fi-steps --format text` in the terminal first, using the detected
conda environment fallback when necessary. Then look at the function
body to decide:
- function calls .initialize() -> "initialize"
- function calls ctx.solver.solve() as the first solve -> "solve_initial"
- function calls .fix() on variables -> "set_operating_conditions"
- function sets scaling factors -> "set_scaling"
- function builds the model -> "build"
- function adds costing -> "add_costing"
- function calls ctx.solver.solve() right after add_costing ->
  "initialize_costing"
- function unfixes variables and adds objective -> "setup_optimization"
- function calls ctx.solver.solve() after unfixing -> "solve_optimization"

Never assign a name not returned by fi-steps. If a function's purpose
is ambiguous, choose the closest valid name from its behavior and
explain the recommended compatibility mapping in the normal plan. Do
not ask the user to design it. For duplicate-purpose phases, use one
decorated adapter that calls the original helpers in runtime order.

Step naming and step ordering are separate decisions. Use `fi-steps`
to validate the name, then place that name according to the original
entry-point execution sequence.

## Runner Variable Name

Both FS and _FS are valid:
- use whatever the original flowsheet uses, or FS if starting fresh
- always pass the approved explicit sequence with
  `FS = FlowsheetRunner(steps=(...))` or
  `_FS = FlowsheetRunner(steps=(...))`

## Context Variable Name

Both ctx and context are valid:
- flash flowsheet and HDA use ctx
- methanol flowsheet uses context
- use whatever the original flowsheet uses, or ctx if starting fresh

## Substeps

Helper functions inside build can optionally be decorated as substeps:
```python
@FS.substep("build", "add_props")
def add_property_packages(m):
    ...
```
Use substeps when the helper functions should be visible to the
Flowsheet Inspector. If they are just internal helpers, leave them
as plain functions called from inside build.

## Wrapping Rules

- never change any flowsheet logic
- preserve the runtime order of the original entry point
- only add decorators, imports, and context handling
- always make a separate set_solver step for the initial solver
- place set_solver at the original initial-solver setup boundary
- preserve later original solver changes before their consuming solve
- always pass the mapped order explicitly to
  `FlowsheetRunner(steps=(...))`
- never create a new SolverFactory inside solve steps
- always use the selected context variable for `tee`, not `tee=True`
- never drop a copied source line except for an explicitly permitted
  wrapper replacement
- preserve all original comments by default; remove an obsolete
  manual-call comment only with explicit user approval
- NEVER use a step name not returned by fi-steps --format text
- use fi-steps only to validate names, never to choose execution order
- never use bare `FlowsheetRunner()` for a multi-step wrapped flowsheet
- plain helper functions and the __main__ block are full plan items
  and require individual confirmation in function-by-function mode
- ALWAYS write to the new wrapped file only — never the original
- ALWAYS ask the user what to name the file before creating it
- ALWAYS create the wrapped file before writing any content to it

## Common Pitfalls

- wrong import path: never use idaes.core.util.structfs — correct
  path is idaes_fi.structfs.fsrunner
- default runner order: bare `FlowsheetRunner()` may execute valid
  steps in an order that differs from the original flowsheet
- confusing names with order: `fi-steps` validates allowed names but
  does not determine the correct order for a particular flowsheet
- reading definition order: derive runtime order from `main()` or the
  equivalent entry point, not from where functions appear in the file
- flattening solver setup: do not move later solver changes into the
  initial `set_solver` step or apply one solver configuration to all solves
- silent phase mapping: do not rename or combine a distinct phase
  without explaining the recommended mapping in the normal plan
- dropping lines: always compare wrapped output against original
  line by line before writing to file
- forgetting context model access: every model-using step except build
  needs the model from the selected context variable as its first line
- wrapping helper functions: add_property_packages, add_units,
  connect_units inside build do NOT get @FS.step — they stay as
  plain functions unless using substep pattern
- inventing step names: using a name not returned by fi-steps will
  cause FlowsheetRunner to throw a KeyError and the flowsheet will
  fail to load. Always run fi-steps first
- skipped steps: when wrapping function by function, always verify
  every step in the approved plan actually appears in the final
  output — it is possible to silently skip a planned step
- claiming verification before content is written: apply the selected
  mode's writing gate before Stage 3
- writing before confirmation in function-by-function mode: never
  write an item before the user confirms it
- editing the original: never make any changes to the original
  flowsheet file — all changes go to the new wrapped file only
- writing without asking filename: always ask the user what to name
  the file before creating it

## File Output

CRITICAL — Never edit the original file directly. Before making
any changes, create a new empty file with the name the user
provided in the same folder as the original. All wrapping changes
go into the new file only. The original file must remain completely
untouched throughout the entire wrapping process.

Ask the user what they want to name the wrapped file after the plan
is confirmed and the mode is selected, but before creating the file:
"What would you like to name the wrapped file? Default is
[original_filename]_wrapped.py"

Wait for the user's response, then create that empty file in the
same folder as the original before writing anything to it.

The only new user-visible file should be the wrapped output `.py`
file. Do not create patch files, chunk files, helper scripts, or
`.codex_*` temporary files in the user's workspace.

In function-by-function mode, show and confirm each item before
writing it. In one-shot mode, write the complete approved plan in one
pass without item-by-item confirmations. Never touch the original in
either mode.

Do not use workspace-visible patch/chunk files
for either mode.

If temporary files are unavoidable, use the system temporary directory
and delete them before responding.

Based only on the original flowsheet imports, tell the user which
environment to activate. Ignore the wrapper-added `idaes_fi` import:
- imports from idaes_examples -> conda activate prommis-dev
- otherwise, imports from prommis, idaes_fi, or plain idaes ->
  conda activate idaes-fi


## Reference

Valid step names: run `fi-steps --format text`, using
`conda run -n <detected-environment>` when necessary
Flowsheet execution order: derive it from the original entry point and
pass it explicitly to `FlowsheetRunner(steps=(...))`
Documentation: docs/usage.md in flowsheet-inspector-lib repo

## Before and After Example

See references/examples.md for the full flash flowsheet before and after.

## Quality Checklist

See references/quality-checklist.md for the diff check and
verification steps to run after wrapping.
