# Quality Checklist

## Contents

- [Mode-specific writing gate](#step--1-mode-specific-writing-gate)
- [Plan completeness](#step-0-plan-completeness-check)
- [Valid step names](#step-05-valid-step-name-check)
- [Execution order](#step-075-execution-order-check)
- [Solver lifecycle](#step-09-solver-lifecycle-parity-check)
- [Source accounting](#step-1-source-accounting-check)
- [Source preservation](#step-2-normalized-source-preservation-check)
- [Imports](#step-3-import-check)
- [Context handling](#step-4-context-check)
- [Bottom of file](#step-5-bottom-of-file-check)
- [Syntax](#step-55-syntax-check)
- [Delivery](#step-6-confirm-file-written)
- [Fallback instructions](#fallback-instructions)
- [Tips for users](#tips-for-users)

## Step -1: Mode-Specific Writing Gate

Run this check before every other checklist step.

Before verification, apply the gate for the selected wrapping mode:

- Function-by-function mode: every plan item has been shown,
  confirmed, and written to the wrapped file.
- One-shot mode: the plan has been approved and every plan item has
  been written to the wrapped file. Item-by-item confirmation is not
  required.

The gate includes imports and runner setup containing the approved
execution order in its explicit `steps=(...)` sequence, every
`@FS.step` function, every plain helper, and the `__main__` block. If
the selected mode's gate is not met, stop, finish writing the missing
content according to that mode, and then repeat Step -1.

## Step 0: Plan Completeness Check

Compare the final wrapped file against the original wrapping plan
from stage 2. Every item listed in the plan — imports and wrapper setup, every
@FS.step function, every plain helper, and the __main__ block —
must appear in the final file. If any planned item is missing,
stop and add it before continuing.
Confirm that the planned runner setup contains the approved explicit
`steps=(...)` sequence; a bare runner is not a complete plan item.

## Step 0.5: Valid Step Name Check

Run `fi-steps --format text` in the terminal to get the current valid
step names. If it is unavailable in the current shell, run
`conda run -n <detected-environment> fi-steps --format text`.
Check every @FS.step("name") in the wrapped file against that list
one by one.

If any step name is not on the list, it WILL cause a KeyError when
the Flowsheet Inspector tries to load the file. Stop immediately and
choose the closest valid name from the phase behavior. If this changes
the approved plan, show the recommended compatibility mapping with one
plain-language explanation in the normal plan. Do not ask the user to
design it. Then rerun Steps 0.5 and 0.75.

Never check against a hardcoded list — always use fi-steps output
since names may change between versions.
Treat `fi-steps` only as the set of valid names. Never use its printed
order to determine or approve the wrapped flowsheet's execution order.

## Step 0.75: Execution Order Check

Extract the actual call sequence from the original `main()` or equivalent
entry point, following any orchestration function it calls. Map each
original phase to its approved wrapped step name.

Construct the expected wrapped order by preserving the relative order of
all original phases, keeping `build` first, and placing the wrapper-only
`set_solver` at the original initial-solver setup boundary before its
consuming solve.

Read the tuple passed to `FlowsheetRunner(steps=(...))` in the wrapped file
and compare it position by position against that expected mapped order.
The check passes only if:

- the runner has an explicit `steps=(...)` sequence
- every planned step appears exactly once
- no unplanned step appears
- every step is in the expected position
- every non-exact step-name mapping matches the recommended mapping
  confirmed through the normal plan

Do not infer execution order from function-definition order, decorator
order, or `fi-steps` output. A bare `FlowsheetRunner()` is an automatic
failure for a multi-step wrapped flowsheet.

If the sequences differ, stop and correct the `steps=(...)` tuple before
continuing. Do not move function bodies merely to make their file order
match. If the original entry point is missing or ambiguous, return to
planning with the best source-supported order and one plain-language
reason. Do not ask the user to design the order.

## Step 0.9: Solver Lifecycle Parity Check

Map each original solve to the solver state immediately before it. The
wrapped file must preserve the solver type, options, conditions, solve
arguments, and any later reconfiguration before the same consuming
solve. The initial `set_solver` must remain at the original solver
setup boundary. Do not invent, remove, consolidate, or reorder
configurations. If the mapping is ambiguous, fail this check and return
to planning with the best source-supported recommendation and one
plain-language reason.

## Step 1: Source Accounting Check

Create an accounting map between the original flowsheet and the
wrapped file. Verify that:

- every original function appears exactly once as a decorated step or
  unchanged plain helper
- every inline model-processing phase from the original entry point
  appears exactly once in a wrapped step
- no distinct phase is renamed or combined without the recommended
  compatibility mapping recorded in the normal plan
- every wrapper-only function, such as `set_solver` or a
  duplicate-purpose adapter, is identified separately
- no original function or inline phase is missing or duplicated

Do not use a simple function-count formula. Wrapping may decompose an
orchestration function or add wrapper-only adapters, so equal counts
do not prove completeness.

## Step 2: Normalized Source Preservation Check

Compare each original function and helper against its wrapped form.
Normalize only these permitted wrapper transformations:

- adding `@FS.step(...)`
- changing a decorated function signature to accept the selected
  `Context` variable
- adding access to the shared model, solver, results, and `tee`
- replacing `return m` with assignment to the selected context model
- replacing local solver creation and solve plumbing with shared
  context operations
- adding the one outer indentation level required by a wrapper
- adding wrapper-only imports, runner setup, adapters, and `run_steps()`

After normalization, all copied imports, comments, blank lines,
spacing, line breaks, statement order, and internal indentation must
match the original. Plain helpers must match exactly unless the user
explicitly approved a change.

If an unapproved difference is found, stop, correct it in the wrapped
file, and identify the corrected source item to the user.

## Step 3: Import Check

Check that the wrapper import is present at the top of the file:
```python
from idaes_fi.structfs.fsrunner import FlowsheetRunner, Context
```

Check that the runner is constructed with an explicit `steps=(...)`
sequence containing the exact order verified in Step 0.75. Reject a bare
`FlowsheetRunner()` for a multi-step wrapped flowsheet.

Check that the original imports are all still present — nothing
should have been removed.

## Step 4: Context Check

For every step that uses the model except build:
- the first executable line must get the model from the selected
  context variable
- solve steps must not create or reconfigure a solver
- any later original solver setup must stay in its approved preceding
  phase and store the active solver in context
- solve calls must use the solver and `tee` setting from that same
  context variable

For build:
- each original `return m` path must be replaced by assignment to the
  selected context model at the equivalent point
- no original `return m` may remain

Plain helper functions are exempt from this check since they keep
their original (m) signature unchanged.

## Step 5: Bottom of File Check

The file must end with the same runner variable used in its runner
declaration. For example:
```python
if __name__ == "__main__":
    FS.run_steps()
```

`_FS.run_steps()` is equally valid when the runner is declared as
`_FS`.

No manual function calls like m = build_model() or solve(m). This
check can only be marked passed if the __main__ block has actually
been written to the file per Step -1.

## Step 5.5: Syntax Check

Parse the complete wrapped file without executing it:

```bash
python -c "import ast, pathlib; ast.parse(pathlib.Path(r'<wrapped-file>').read_text(encoding='utf-8'))"
```

The check passes only if parsing completes without a `SyntaxError`.
Keep this check read-only; do not run a formatter or import sorter.

## Step 6: Confirm File Written

After all checks pass, confirm to the user that the wrapped file
has been written successfully. Tell the user:
- the exact filename and folder it was saved to
- which conda environment to activate, based only on the original
  flowsheet imports and not the wrapper-added `idaes_fi` import

Use `prommis-dev` when the original imports `idaes_examples`.
Otherwise, use `idaes-fi` when it imports `prommis`, `idaes_fi`, or
plain `idaes`.

Do not output the whole file as a code block — it is already written
to disk.

## Fallback Instructions

### If a function was written incorrectly to the file:
Fix the specific lines directly in the file. Show the user only the
corrected lines, not the whole function again.

### If the user provides only a filename:
Read the file directly and complete stage 1 from its contents. Ask the
user about functions, costing, optimization, or operating conditions
only when the file cannot be read or the information is ambiguous.

### If user provides a partially wrapped flowsheet:
Read the file, check what is already correct, identify what is
missing or wrong, fix only those parts directly in the file.

### If a step name is not on the fi-steps list:
Stop immediately. Choose the closest valid name from the phase
behavior. If the plan changes, show the recommended compatibility
mapping with one plain-language explanation in the normal plan. Do not
ask the user to design it. Then rerun Steps 0.5 and 0.75.

### If the wrapped execution order differs from the original:
Stop immediately. Re-extract the original entry-point call sequence,
map it to the approved step names, place the wrapper-only `set_solver`
at the original initial-solver boundary, and correct only the runner's
`steps=(...)` tuple. Re-run Steps 0.5 and 0.75 before continuing.

### If Stage 3 is reached before the writing gate is met:
Stop immediately. Identify the missing plan items and finish them
according to the selected mode. In function-by-function mode, show and
confirm them first. In one-shot mode, write the missing approved plan
items without adding item-by-item confirmation.


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

If the AI uses the right names in the wrong order: "Compare the explicit
runner steps against the call order in the original main function."

If the AI claims verification passed for content not yet written:
"You haven't written [item] to the file yet, do that before claiming
any checks passed."
