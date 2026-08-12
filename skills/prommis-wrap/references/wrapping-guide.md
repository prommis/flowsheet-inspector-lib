# Wrapping Reference Guide

## Contents

- [Plan and approval](#step-0--plan-then-approve)
- [Protect the original file](#critical--never-edit-the-original-file)
- [Runner and step constants](#critical--runner-and-step-constants)
- [Step purposes](#what-each-step-does)
- [Solver lifecycle](#preserve-solver-lifecycle)
- [Step-selection decision tree](#decision-tree--which-steps-to-include)
- [Wrapping modes](#wrapping-mode-procedures)
- [Context handling](#context-handling)
- [Wrapping rules](#wrapping-rules)
- [Common pitfalls](#common-pitfalls)
- [File output](#file-output)
- [References and examples](#reference)

## Step 0 -- Plan Then Approve

Before wrapping anything, show the user a plan. The plan must list every
single piece of the final file, not just the `@FS.step` decorated
functions. This includes:

- imports and wrapper setup: `FlowsheetRunner`, `Context`, `Steps`, and
  bare `FS = FlowsheetRunner()`
- every function getting an `@FS.step(Steps.<name>)` decorator
- every plain helper function that stays undecorated, such as `report`
- the final `__main__` block with the selected runner's `run_steps()`

Do not include an explicit `steps=(...)` sequence in the plan or in the
wrapped file. A structured flowsheet follows the standard
FlowsheetRunner step order.

With the plan, offer two wrapping modes:
1. Function-by-function mode: show, confirm, and write each plan item individually.
2. One-shot mode: write the complete approved plan in one pass, then run the quality checklist without item-by-item confirmations.

After listing all plan items, count them explicitly and state the total:
"Total plan items: X".

Example:
"I found 4 functions in flash_flowsheet.py. Here is my wrapping plan:
- imports and wrapper setup -> add FlowsheetRunner, Context, Steps, and FS = FlowsheetRunner()
- build_model -> @FS.step(Steps.build)
- set_solver -> wrapper-only @FS.step(Steps.set_solver)
- set_operating_conditions -> @FS.step(Steps.set_operating_conditions)
- init_model -> @FS.step(Steps.initialize)
- solve -> @FS.step(Steps.solve_initial)
- __main__ block -> replaced with FS.run_steps()
Total plan items: 7
Confirm this plan and choose function-by-function or one-shot mode."

After plan confirmation and mode selection, ask what to name the wrapped
file. Create that empty file in the same folder as the original. All
wrapped content goes into this new file only.

## CRITICAL -- Never Edit the Original File

All wrapping changes go into the new wrapped file only. The original file
must remain completely untouched.

## CRITICAL -- Runner and Step Constants

Always add these wrapper imports:

```python
from idaes_fi.structfs.fsrunner import FlowsheetRunner, Context
from idaes_fi.structfs.common import Steps
```

Always instantiate the runner without an explicit step list:

```python
FS = FlowsheetRunner()
```

Do not pass a `steps` argument to `FlowsheetRunner`.

Always use `Steps` constants in decorators:

```python
@FS.step(Steps.build)
def build_model(ctx: Context):
    ...
```

Do not use quoted string step names in decorators.

Both `FS` and `_FS` are valid runner variable names. Use whatever the
original flowsheet already uses, or `FS` if starting fresh.

## What Each Step Does

build -- creates `ConcreteModel`, `FlowsheetBlock`, and unit models.
Stores the model in the selected context variable. Never returns `m`.

set_solver -- creates the initial solver and stores it in context. It
must not read `ctx.model` unless the original solver setup actually used
the model object.

set_operating_conditions -- fixes input variables with `.fix()` calls.

set_scaling -- sets manual scaling factors on variables and constraints.

initialize -- initializes unit models before solving.

solve_initial -- solves the flowsheet at fixed operating conditions.

set_autoscaling -- applies automatic scaling after the initial solve.

add_costing -- adds costing blocks to the flowsheet.

initialize_costing -- initializes costing blocks.

setup_optimization -- unfixes variables and adds an objective function.

solve_optimization -- solves the optimization problem.

## Preserve Solver Lifecycle

Trace each original solver creation or reconfiguration to the solve that
consumes it. Use `set_solver` for the initial setup at its original
boundary; keep later changes in their original phase and store the
active solver in context.

Correct `set_solver` examples:

```python
@FS.step(Steps.set_solver)
def set_solver(ctx: Context):
    ctx.solver = get_solver()
```

```python
@FS.step(Steps.set_solver)
def set_solver(ctx: Context):
    optarg = {"tol": 1e-6, "max_iter": 500}
    ctx.solver = get_solver()
    ctx.solver.options = optarg
```

Do not add this line unless `m` is actually used:

```python
m = ctx.model
```

## Decision Tree -- Which Steps to Include

Does the flowsheet build a model?
- Yes -> wrap the build phase as `@FS.step(Steps.build)`.

Does the original create a solver before solving?
- Yes -> add a wrapper-only `@FS.step(Steps.set_solver)` step.

Does it fix operating conditions?
- Yes -> wrap that phase as `@FS.step(Steps.set_operating_conditions)`.

Does it set scaling factors?
- Yes -> wrap that phase as `@FS.step(Steps.set_scaling)`.

Does it initialize unit models?
- Yes -> wrap it as `@FS.step(Steps.initialize)`.

Does it solve a fixed operating-condition model?
- Yes -> wrap the solve as `@FS.step(Steps.solve_initial)`.

Does it add costing?
- Yes -> include `@FS.step(Steps.add_costing)` and, if present,
  `@FS.step(Steps.initialize_costing)`.

Does it set up an optimization objective or unfix optimization variables?
- Yes -> include `@FS.step(Steps.setup_optimization)`.

Does it solve the optimization problem?
- Yes -> include `@FS.step(Steps.solve_optimization)`.

Does it have plain helper functions called from inside steps?
- Yes -> include them as plan items and keep them undecorated.

If multiple original functions logically belong to the same standard
step, keep those original functions as plain helpers and create one
small decorated adapter that calls them in the original runtime order.

## Wrapping Mode Procedures

Count all plan items regardless of mode. File length may inform the
recommendation, but the user selects the mode.

### Function-by-Function Mode

- create the empty named wrapped file after plan approval
- handle exactly one plan item at a time
- show the item and ask for confirmation
- write only the confirmed item to the wrapped file
- continue until every plan item is confirmed and written
- run the complete quality checklist

### One-Shot Mode

- create the empty named wrapped file after plan approval
- treat the approved plan as the content confirmation
- write every plan item to the wrapped file in one pass
- do not request item-by-item confirmations
- run the complete quality checklist against the written file

## Context Handling

For build:
- replace each original `return m` with assignment to the selected
  context model, such as `ctx.model = m`
- do not leave `return m` in the wrapped build step

For steps that use the model:
- get the model from context at the first point it is needed, usually
  `m = ctx.model`

For `set_solver`:
- do not add `m = ctx.model` unless the original solver setup actually
  used the model
- create/configure the solver and store it in context
- do not solve the model

For solve steps:
- do not create a new local solver
- call `ctx.solver.solve(...)`
- use `tee=ctx["tee"]`, not `tee=True`
- store results in context when possible

Plain helper functions keep their original signature and body unless the
user explicitly approves a change.

## Wrapping Rules

- never change flowsheet logic
- preserve copied-code formatting exactly except for permitted wrapper transformations
- always use `FS = FlowsheetRunner()` or `_FS = FlowsheetRunner()`
- never pass `steps=(...)` to `FlowsheetRunner`
- always import `Steps` from `idaes_fi.structfs.common`
- always use `@FS.step(Steps.<name>)`
- never use string step names in decorators
- always make a separate `set_solver` step for the initial solver
- never add unused `m = ctx.model` in `set_solver`
- preserve later original solver changes before their consuming solve
- never create a new `SolverFactory` inside solve steps
- always use the selected context variable for `tee`, not `tee=True`
- never drop copied source lines except for explicitly permitted wrapper replacements
- preserve original comments by default
- always write to the new wrapped file only, never the original
- always ask what to name the wrapped file before creating it

## Common Pitfalls

- wrong import path: never use `idaes.core.util.structfs`; use
  `idaes_fi.structfs.fsrunner`
- missing `Steps` import
- explicit runner steps: do not pass a `steps` argument to `FlowsheetRunner`
- string decorators: do not use quoted step names
- unused solver model variable: do not add `m = ctx.model` in
  `set_solver` unless it is actually used
- wrapping helper functions that should stay plain
- dropped source lines
- editing the original file

## File Output

The only new user-visible file should be the wrapped output `.py` file.
Do not create patch files, chunk files, helper scripts, or `.codex_*`
temporary files in the user's workspace.

If temporary files are unavoidable, use the system temporary directory and
delete them before responding.

Based only on the original flowsheet imports, tell the user which
environment to activate. Ignore the wrapper-added `idaes_fi` import:
- imports from `idaes_examples` -> `conda activate prommis-dev`
- otherwise, imports from `prommis`, `idaes_fi`, or plain `idaes` ->
  `conda activate idaes-fi`

## Reference

See `references/examples.md` for a complete before/after example.
See `references/quality-checklist.md` for verification checks to run
after wrapping.
