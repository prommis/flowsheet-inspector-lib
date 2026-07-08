# Quality Checklist

## Step -1: Confirmed Content Check (run before everything else)

Before doing any verification, check: has every single item from the
stage 2 plan actually been shown, confirmed, and written to the file?
This includes every @FS.step function, every plain helper function
(e.g. report), the steps= ordering tuple if present, and the
__main__ block.

If any plan item has NOT been shown, confirmed, and written yet,
STOP. Do not proceed to any other check. Show the missing item(s)
first, get confirmation, write it to the file, then return to
Step -1 and re-check.

A checklist item marked as passed for content that was never actually
shown, confirmed, and written to the file is a false pass and is not
acceptable.

## Step 0: Plan Completeness Check

Compare the final wrapped file against the original wrapping plan
from stage 2. Every item listed in the plan — every @FS.step function,
every plain helper, the steps= ordering tuple, and the __main__ block
— must appear in the final file. If any planned item is missing,
stop and add it before continuing.

## Step 0.5: Valid Step Name Check

Run `fi-steps --format text` directly in the terminal to get the
current valid step names for the installed version of idaes-fi.
Check every @FS.step("name") in the wrapped file against that list
one by one.

If any step name is not on the list, it WILL cause a KeyError when
the Flowsheet Inspector tries to load the file. Stop immediately and
fix it in the file directly — rename it to the closest valid name
before continuing.

Never check against a hardcoded list — always use fi-steps output
since names may change between versions.

Also check every name inside the steps= tuple against fi-steps output.

## Step 0.75: Step Ordering Check

If the flowsheet has both an initialize step AND a
set_operating_conditions step, check that FlowsheetRunner() was
created with an explicit steps= tuple.

If steps= is missing in this case, STOP. The flowsheet will fail to
run correctly because the default canonical order runs initialize
before set_operating_conditions, causing an InitializationError.
Add the explicit steps= tuple directly to the file before continuing,
placing set_operating_conditions and set_scaling before initialize.

## Step 1: Function Count Check

Count the number of functions in the original flowsheet. Count the
number of @FS.step decorated functions plus plain helpers in the
wrapped file. These must match (plus one for the new set_solver
step if it didn't exist before, minus one if main was deleted and
decomposed into multiple steps).

If they don't match, stop and tell the user: "Function count
mismatch — original has X functions, wrapped file has Y. Something
was dropped. Let me check which one."

## Step 2: Line by Line Diff Check

For each function and helper, compare the wrapped version against
the original:
- every line in the original must appear in the wrapped version
- the only new lines allowed are:
  - @FS.step("name") decorator
  - def function(ctx: Context): signature change
  - m = ctx.model as first line
  - ctx.model = m replacing return m in build
  - ctx.solver = SolverFactory("ipopt") or get_solver() in set_solver
  - ctx["results"] = ctx.solver.solve(m, tee=ctx["tee"]) in solve steps
  - FS.run_steps() at the bottom
  - from idaes_fi.structfs.fsrunner import FlowsheetRunner, Context
  - FS = FlowsheetRunner() or FS = FlowsheetRunner(steps=(...))

Plain helper functions (e.g. report) should have ZERO changes from
the original — not even a signature change.

If any original line is missing, fix it directly in the file —
show the user exactly which line was dropped and where it was added.

## Step 3: Import Check

Check that these two lines are present at the top of the file:
```python
from idaes_fi.structfs.fsrunner import FlowsheetRunner, Context
FS = FlowsheetRunner()
```
or, if explicit ordering is needed:
```python
from idaes_fi.structfs.fsrunner import FlowsheetRunner, Context
FS = FlowsheetRunner(steps=(...))
```

Check that the original imports are all still present — nothing
should have been removed.

## Step 4: Context Check

For every step except build:
- first line must be m = ctx.model
- no new SolverFactory() calls
- solve calls must use ctx.solver.solve(m, tee=ctx["tee"])

For build:
- last line must be ctx.model = m
- no return m

Plain helper functions are exempt from this check since they keep
their original (m) signature unchanged.

## Step 5: Bottom of File Check

The file must end with:
```python
if __name__ == "__main__":
    FS.run_steps()
```

No manual function calls like m = build_model() or solve(m). This
check can only be marked passed if the __main__ block has actually
been written to the file per Step -1.

## Step 6: Confirm File Written

After all checks pass, confirm to the user that the wrapped file
has been written successfully. Tell the user:
- the exact filename and folder it was saved to
- which conda environment to activate before running it
- the known idaes-fi 0.1.0 _solver_out bug: if a step fails you may
  see "AttributeError: 'NoneType' object has no attribute 'flush'" —
  this is a library bug, debug the actual failed step instead

Do not output the whole file as a code block — it is already written
to disk.

## Fallback Instructions

### If a function was written incorrectly to the file:
Fix the specific lines directly in the file. Show the user only the
corrected lines, not the whole function again.

### If user skips stage 1:
Ask: "How many functions does the flowsheet have? Does it have costing
or optimization steps? Does it fix operating conditions before
initializing?"

### If user provides a partially wrapped flowsheet:
Read the file, check what is already correct, identify what is
missing or wrong, fix only those parts directly in the file.

### If a step name is not on the fi-steps list:
Stop immediately. Fix it directly in the file. Tell the user:
"[step_name] is not a valid FlowsheetRunner step name for this
idaes-fi version. I have renamed it to [closest_valid_name] —
confirm this is acceptable."

### If Stage 3 is reached before all plan items are written:
Stop immediately. Tell the user: "Stage 3 cannot run yet —
[item name(s)] have not been confirmed and written. Writing them
now before verification."

### If the flowsheet fails with InitializationError after running:
Check whether FlowsheetRunner() has an explicit steps= tuple. If
missing, add it directly to the file with set_operating_conditions
and set_scaling before initialize.

### If the flowsheet fails with AttributeError on _solver_out.flush():
This is the known idaes-fi 0.1.0 library bug. Tell the user to look
at what step actually failed rather than this error message.

## Tips for Users

If the AI is going too fast: "Slow down, show me one function at a time."

If the AI asks too many questions: "Let's focus on essentials only."

If the AI drops lines from a function: "You dropped lines from
[function name], here is the original, please redo just that function."

If the AI wraps a helper function it shouldn't: "That function is a
helper inside build, don't wrap it with @FS.step, leave it as a
plain function."

If the AI invents a step name: "That step name isn't valid — run
fi-steps --format text to get the valid names for this version."

If the AI claims verification passed for content not yet written:
"You haven't written [item] to the file yet, do that before claiming
any checks passed."

If you want to skip verification: "Skip the diff check and just
write the final file."