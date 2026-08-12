# Quality Checklist

## Contents

- [Mode-specific writing gate](#step--1-mode-specific-writing-gate)
- [Plan completeness](#step-0-plan-completeness-check)
- [Runner and step constants](#step-05-runner-and-step-constants-check)
- [Source accounting](#step-1-source-accounting-check)
- [Source preservation](#step-2-normalized-source-preservation-check)
- [Imports](#step-3-import-check)
- [Solver lifecycle](#step-35-solver-lifecycle-parity-check)
- [Context handling](#step-4-context-check)
- [Bottom of file](#step-5-bottom-of-file-check)
- [Syntax](#step-55-syntax-check)
- [Delivery](#step-6-confirm-file-written)
- [Fallback instructions](#fallback-instructions)

## Step -1: Mode-Specific Writing Gate

Run this check before every other checklist step.

- Function-by-function mode: every plan item has been shown, confirmed,
  and written to the wrapped file.
- One-shot mode: the plan has been approved and every plan item has
  been written to the wrapped file.

The gate includes imports and runner setup, every `@FS.step` function,
every plain helper, and the `__main__` block.

## Step 0: Plan Completeness Check

Compare the final wrapped file against the original wrapping plan. Every
planned item must appear in the final file.

## Step 0.5: Runner and Step Constants Check

Check that the wrapper imports are present:

```python
from idaes_fi.structfs.fsrunner import FlowsheetRunner, Context
from idaes_fi.structfs.common import Steps
```

Check that the runner is bare:

```python
FS = FlowsheetRunner()
```

`_FS = FlowsheetRunner()` is also valid.

Fail if the wrapped file passes a `steps` argument to `FlowsheetRunner`.

Check every decorated step. It must use a `Steps` constant:

```python
@FS.step(Steps.build)
```

Fail if any decorated step uses a quoted string literal instead of a `Steps` constant.

## Step 1: Source Accounting Check

Verify that:

- every original function appears exactly once as a decorated step or
  unchanged plain helper
- every inline model-processing phase from the original entry point
  appears exactly once in a wrapped step
- every wrapper-only function, such as `set_solver`, is identified separately
- no original function or inline phase is missing or duplicated

## Step 2: Normalized Source Preservation Check

Compare each original function and helper against its wrapped form.
Normalize only these permitted wrapper transformations:

- adding `@FS.step(Steps.<name>)`
- changing a decorated function signature to accept the selected
  `Context` variable
- adding access to the shared model, solver, results, and `tee`
- replacing `return m` with assignment to the selected context model
- replacing local solver creation and solve plumbing with shared context operations
- adding the one outer indentation level required by a wrapper
- adding wrapper-only imports, runner setup, adapters, and `run_steps()`

Plain helpers must match exactly unless the user explicitly approved a
change.

## Step 3: Import Check

Check that all original imports are still present and that wrapper-only
imports are present:

```python
from idaes_fi.structfs.fsrunner import FlowsheetRunner, Context
from idaes_fi.structfs.common import Steps
```

## Step 3.5: Solver Lifecycle Parity Check

Map each original solve to the solver state immediately before it. The
wrapped file must preserve solver type, options, conditions, solve
arguments, and later reconfiguration before the same consuming solve.

The initial `set_solver` step should create/configure the solver and
store it in context. It must not solve the model.

## Step 4: Context Check

For build:
- each original `return m` path must be replaced by assignment to the
  selected context model
- no original `return m` may remain

For every step that uses the model except build:
- get the model from the selected context variable when needed
- solve steps must not create or reconfigure a solver
- solve calls must use the solver and `tee` setting from context

For `set_solver`:
- it must create/configure the solver and store it in context
- it must not include `m = ctx.model` unless `m` is actually used by the
  original solver setup
- it must not solve the model

Plain helper functions are exempt.

## Step 5: Bottom of File Check

The file must end with the same runner variable used in its runner
declaration:

```python
if __name__ == "__main__":
    FS.run_steps()
```

`_FS.run_steps()` is equally valid when the runner is declared as `_FS`.

## Step 5.5: Syntax Check

Parse the complete wrapped file without executing it:

```bash
python -c "import ast, pathlib; ast.parse(pathlib.Path(r'<wrapped-file>').read_text(encoding='utf-8'))"
```

Do not run a formatter or import sorter.

## Step 6: Confirm File Written

After all checks pass, tell the user:

- the exact filename and folder it was saved to
- which conda environment to activate, based only on original imports

Use `prommis-dev` when the original imports `idaes_examples`. Otherwise,
use `idaes-fi` when it imports `prommis`, `idaes_fi`, or plain `idaes`.

Do not output the whole file as a code block.

## Fallback Instructions

If a function was written incorrectly, fix the specific lines directly
in the wrapped file and show only the corrected lines.

If the user provides only a filename, read the file directly and
complete Stage 1 from its contents.

If the user provides a partially wrapped flowsheet, read the file,
identify what is missing or wrong, and fix only those parts.

If Stage 3 is reached before the writing gate is met, stop and finish
the missing plan items according to the selected mode.
