# Wrapping Reference Guide

## Step 0 — Plan Then Approve

Before wrapping anything, show the user a plan. The plan must list
every single piece of the final file that needs to be shown and
confirmed — not just the @FS.step decorated functions. This includes:
- every function getting a @FS.step decorator
- every plain helper function that stays undecorated (e.g. report)
- the steps= ordering tuple passed to FlowsheetRunner() if needed
- the final __main__ block with FS.run_steps()

All four categories count as items in the plan and must each be
shown and confirmed individually during stage 2, in the same way.

After listing all plan items, count them explicitly and state the
total: "Total plan items to show and confirm: X". Then verify that
count matches the actual number of rows in the plan table before
asking for confirmation. If the count is wrong, correct it before
proceeding — a wrong count at stage 2 will cause a false-complete
signal at stage 3.

Example:
"I found 4 functions in flash_flowsheet.py. Here is my wrapping plan:
- imports block -> shown unchanged for confirmation
- steps= tuple on FlowsheetRunner() -> explicit ordering required
- build_model -> @FS.step("build")
- set_operating_conditions -> @FS.step("set_operating_conditions")
- init_model -> @FS.step("initialize")
- solve -> @FS.step("solve_initial")
- adding new set_solver step
- __main__ block -> replaced with FS.run_steps()
Total plan items to show and confirm: 8
Confirm to proceed."

If the flowsheet has a plain helper function like report(m) that is
called from steps but not itself decorated, list it explicitly:
"- report(m) -> stays as plain helper, no decorator, shown unchanged
  for confirmation"

Wait for user confirmation before wrapping.

After plan confirmation, immediately ask the user what to name the
wrapped file before writing anything:
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

## CRITICAL — FlowsheetRunner Does Not Run Steps in File Order

FlowsheetRunner executes steps in its own internal FIXED canonical
order by default, NOT the order functions appear in the file and NOT
the order @FS.step decorators were applied. The default canonical
order runs `initialize` BEFORE `set_operating_conditions` and
`set_scaling`.

This breaks any flowsheet that fixes its feed/inputs inside
set_operating_conditions, because the units would be initialized
before their inlets are fixed, causing an InitializationError. This
is the normal case for almost every PrOMMiS/IDAES flowsheet.

To fix this, always pass an explicit `steps=` tuple to
`FlowsheetRunner()` specifying the correct execution order for this
specific flowsheet. The tuple must use only valid step names from
the installed idaes-fi version — run `fi-steps --format text`
directly in the terminal to get the current list.

Always add the following comment block above the steps= tuple,
customized to explain why this specific flowsheet needs explicit
ordering:

```python
# NOTE: fi-run executes steps in a FIXED canonical order, NOT the order the
# @FS.step functions appear in this file. The default order runs `initialize`
# BEFORE `set_operating_conditions`/`set_scaling`, which breaks any flowsheet
# that fixes its feed/inputs in `set_operating_conditions` (the units would be
# initialized before their inlets are fixed -> InitializationError). We pass an
# explicit `steps=` order so inputs and scaling happen before initialization.
FS = FlowsheetRunner(
    steps=(
        "build",
        "set_solver",
        "set_operating_conditions",  # fix feeds/inputs first (DOF -> 0)
        "set_scaling",                # then apply scaling
        "initialize",                 # only now initialize the units
        "solve_initial",
        "add_costing",
        "initialize_costing",
        "setup_optimization",
        "solve_optimization",
    )
)
```

This is required any time the flowsheet has an initialize step AND
fixes operating conditions — which is nearly every PrOMMiS flowsheet.
Always include it unless the flowsheet has no initialize step at all.

## CRITICAL — Valid Step Names Are Not Fixed in Code

The valid step names are defined by the installed version of idaes-fi.
Run this directly in the terminal to get the current list:

```bash
fi-steps --format text
```

Run this yourself — do not ask the user to run it. This outputs all
valid step names in the correct canonical order. Never hardcode this
list — always check against fi-steps output since names may change
between versions. For reference, the list as of idaes-fi 0.1.0 is:
build, set_solver, initialize, set_operating_conditions, set_scaling,
solve_initial, set_autoscaling, add_costing, initialize_costing,
setup_optimization, solve_optimization.

Documentation: docs/usage.md in the flowsheet-inspector-lib repo.

If a function's purpose does not perfectly match any valid name,
assign it to the closest valid name anyway — do not invent custom
names. The tool will reject anything not returned by fi-steps.

If a function genuinely does not fit any valid purpose, flag this to
the user explicitly: "This function doesn't match any standard step
name. The closest fit is [name], but note this may not be fully
accurate. Confirm this is acceptable, or let me know how you'd like
it handled."

## Standard Step Order

Run `fi-steps --format text` directly in the terminal to get the
canonical step order for your installed version. For reference, the
order as of idaes-fi 0.1.0:

build -> set_solver -> initialize -> set_operating_conditions ->
set_scaling -> solve_initial -> set_autoscaling -> add_costing ->
initialize_costing -> setup_optimization -> solve_optimization

Note: not every flowsheet has all steps. Only include steps that
exist in the original flowsheet.

If two original functions both logically belong to the same valid
step name (e.g. two separate solve calls), assign the second one to
the closest available valid name — for example initialize_costing for
a second solve that happens after costing is added — rather than
inventing a new name.

## What Each Step Does

build — creates ConcreteModel, FlowsheetBlock, and all unit models.
Stores model in ctx.model at the end. Never returns m.

set_solver — creates IPOPT solver and stores in ctx.solver. Always a
separate step, never create SolverFactory inside another step.

set_operating_conditions — fixes all input variables with .fix() calls.
This is where parameter changes happen. Must run before initialize
if the flowsheet has one.

initialize — initializes unit models before solving. Not always
present. Must run after set_operating_conditions and set_scaling
when explicit steps= ordering is set.

set_scaling — sets manual scaling factors on variables and constraints.
Should run before initialize.

solve_initial — solves the flowsheet at fixed operating conditions.
Always uses ctx.solver.solve(m, tee=ctx["tee"]).

set_autoscaling — applies automatic scaling after the initial solve.

add_costing — adds costing blocks to the flowsheet.

initialize_costing — initializes the costing blocks. Also use this
name for any second solve that happens immediately after add_costing,
even if the function is actually re-solving the model rather than
literally initializing anything. This is the closest valid step name
available for that purpose.

setup_optimization — unfixes variables and adds an objective function.

solve_optimization — solves the optimization problem.

## Decision Tree — Which Steps to Include

Does the flowsheet have an initialize function?
- Yes -> wrap it as @FS.step("initialize"). Always set explicit steps=
  ordering so it runs after set_operating_conditions and set_scaling.

Does the flowsheet have costing?
- Yes -> include add_costing and initialize_costing
- No -> skip those steps

Does the flowsheet have an optimization objective?
- Yes -> include setup_optimization and solve_optimization
- No -> skip those steps

Is it a simple simulation?
- Yes -> build, set_solver, set_operating_conditions, set_scaling,
  solve_initial only

Does the flowsheet have plain helper functions called from inside
steps (e.g. report(m))?
- Yes -> include them as items in the plan, show them unchanged for
  confirmation just like any decorated step, even though they get
  no @FS.step decorator

## Decision Tree — How to Handle Flowsheet Length

Count the total number of plan items first — this means @FS.step
functions PLUS plain helper functions PLUS the __main__ block PLUS
the steps= ordering tuple if needed:

3 or fewer total plan items:
- wrap everything, checking each step name against fi-steps output
  as it is assigned
- include explicit steps= ordering if the flowsheet has both
  set_operating_conditions and initialize
- show the complete wrapped content to the user
- ask: "Does this look correct? If yes, what would you like to name
  the wrapped file? Default is [original_filename]_wrapped.py"
- wait for the user's response
- create the file with that name in the same folder as the original
- write all content to the new file
- then run the full checklist in references/quality-checklist.md
  before confirming done

More than 3 total plan items:
- warn the user upfront: "This flowsheet has X items to wrap and
  confirm so I will go one at a time. Confirm to continue."
- after plan confirmation, immediately ask what to name the wrapped
  file before writing anything:
  "What would you like to name the wrapped file? Default is
  [original_filename]_wrapped.py"
- create that empty file in the same folder as the original
- wrap exactly ONE item per response, nothing else
- before sending the response, if the item is a @FS.step function,
  check the step name just assigned against fi-steps output. If it
  is not valid, fix it before sending
- show the wrapped item to the user
- ask: "Does this look correct? If yes I will add it to the wrapped
  file — confirm to proceed."
- wait for confirmation before writing anything to the file
- write ONLY that confirmed item to the wrapped file, then move
  to the next item
- never write to the wrapped file without explicit confirmation
- never touch the original file at any point
- never include more than one item in a single response
- DO NOT begin Stage 3 verification until every single item in the
  plan has been individually shown, confirmed, and written to the
  wrapped file
- after all items are confirmed and written, run the full checklist
  in references/quality-checklist.md against the complete wrapped file

## How to Name Each Step

Run `fi-steps --format text` directly in the terminal first to get
the valid names for the installed version. Then look at the function
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
is ambiguous, choose the closest valid name and explain the reasoning
to the user.

## Runner Variable Name

Both FS and _FS are valid:
- flash flowsheet uses FS = FlowsheetRunner()
- template uses _FS = FlowsheetRunner()
- use whatever the original flowsheet uses, or FS if starting fresh

When steps= ordering is needed, it goes inside the same call:
```python
FS = FlowsheetRunner(steps=(...))
```

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
- only add decorators, imports, and context handling
- always make a separate set_solver step
- never create a new SolverFactory inside solve steps
- always use tee=ctx["tee"] not tee=True in solve_initial
- never drop any lines from the original functions
- keep all original comments that still apply
- remove only comments that reference the old manual call pattern
- NEVER use a step name not returned by fi-steps --format text
- plain helper functions and the __main__ block are full plan items
  requiring individual confirmation, not implicit afterthoughts
- ALWAYS set explicit steps= ordering on FlowsheetRunner() when the
  flowsheet has both set_operating_conditions and initialize
- ALWAYS write to the new wrapped file only — never the original
- ALWAYS ask the user what to name the file before creating it
- ALWAYS create the wrapped file before writing any content to it

## Common Pitfalls

- wrong import path: never use idaes.core.util.structfs — correct
  path is idaes_fi.structfs.fsrunner
- dropping lines: always compare wrapped output against original
  line by line before writing to file
- forgetting m = ctx.model: every step except build needs this as
  the first line
- wrapping helper functions: add_property_packages, add_units,
  connect_units inside build do NOT get @FS.step — they stay as
  plain functions unless using substep pattern
- inventing step names: using a name not returned by fi-steps will
  cause FlowsheetRunner to throw a KeyError and the flowsheet will
  fail to load. Always run fi-steps first
- skipped steps: when wrapping function by function, always verify
  every step in the approved plan actually appears in the final
  output — it is possible to silently skip a planned step
- claiming verification before showing content: never run Stage 3
  verification for content that has not actually been shown,
  confirmed, and written to the file
- forgetting steps= ordering: if FlowsheetRunner() is created without
  an explicit steps= tuple, it defaults to running initialize before
  set_operating_conditions and set_scaling, which causes an
  InitializationError on most flowsheets
- writing before confirmation: never write any item to the file
  before the user explicitly confirms it looks correct
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

The workflow for each confirmed item is:
1. Show the wrapped item to the user
2. Ask: "Does this look correct? If yes I will add it to the
   wrapped file — confirm to proceed."
3. After confirmation, write that item to the wrapped file only
4. Never touch the original file at any point

Ask the user what they want to name the wrapped file right after
the plan is confirmed and before creating the file:
"What would you like to name the wrapped file? Default is
[original_filename]_wrapped.py"

Wait for the user's response, then create that empty file in the
same folder as the original before writing anything to it.

Based on the file's imports, tell the user which environment to
activate before running the wrapped flowsheet:
- imports from idaes_examples -> conda activate prommis-dev
- imports from prommis or idaes_fi -> conda activate idaes-fi

Also tell the user about the known idaes-fi 0.1.0 _solver_out bug:
if a step fails during a run, the runner's internal error handling
may throw "AttributeError: 'NoneType' object has no attribute 'flush'"
in idaes_fi/structfs/actions/solver.py. This is a known library bug —
the underlying step failure is the real thing to debug.

## Reference

Valid step names: run `fi-steps --format text` directly in terminal
Full step order: run `fi-steps --format text` directly in terminal
Documentation: docs/usage.md in flowsheet-inspector-lib repo
Known bug: _solver_out AttributeError in idaes-fi 0.1.0

## Before and After Example

See references/examples.md for the full flash flowsheet before and after.

## Quality Checklist

See references/quality-checklist.md for the diff check and
verification steps to run after wrapping.