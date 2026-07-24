# IPOPT Result Guide

Use this guide after a run produces a structured solver result or positively identified IPOPT log. Show the user only the final result needed for the next decision; retain the complete log internally.

## Source priority

Prefer the structured Pyomo result:

```python
from pyomo.opt import check_optimal_termination

ok = check_optimal_termination(results)
status = results.solver.status
termination = results.solver.termination_condition
message = results.solver.message
```

Use the exact IPOPT `EXIT:` line as supporting evidence when captured. If structured and console results differ, report both and do not silently choose one.

## User-facing result translations

### Optimal solution

Examples include `optimal` and `EXIT: Optimal Solution Found`.

```text
What this means: The flowsheet solved successfully.
```

Continue with DiagnosticsToolbox. A successful solve does not erase diagnostic warnings.

### Local infeasibility

Example: `EXIT: Converged to a point of local infeasibility. Problem may be infeasible.`

```text
What this means: The flowsheet ran, but it could not find values that satisfy all active equations and bounds.
```

Next check: use the installed DiagnosticsToolbox report, prioritizing variables at/outside bounds and structural warnings before large residuals.

### Maximum iterations

Example: `EXIT: Maximum Number of Iterations Exceeded`.

```text
What this means: The flowsheet stopped before finding a solution.
```

Next check: inspect DiagnosticsToolbox for extreme values, scaling warnings, bounds, and large residuals before proposing a larger iteration limit.

### Restoration failed

Example: `EXIT: Restoration Failed`.

```text
What this means: The flowsheet could not recover a set of values that satisfies its equations.
```

Next check: run structural diagnostics first, then inspect bounds and evaluation errors from the retained state.

### Evaluation error

Examples include `EXIT: Error in AMPL Evaluation` or an IPOPT evaluation failure.

```text
What this means: A calculation received an invalid value, such as division by zero or a logarithm of a nonpositive number.
```

Next check: `display_potential_evaluation_errors()` when recommended and available, followed by the variables used by the reported expressions.

### Other or unfamiliar termination

Show the exact structured status, termination condition, and message. Explain only what those values establish. Do not convert an unfamiliar result into one of the common categories above.

## Iteration-log clues

Do not show the iteration table unless the user asks. Internally, it can help select a check:

- constraint violation that stops improving can justify checking bounds and large residuals;
- restoration iterations justify structural and evaluation-error checks;
- persistent regularization can justify structural or scaling diagnostics;
- repeated tiny steps or many line searches can justify bounds, extreme-value, or scaling checks.

These patterns are clues, not proof of a root cause. Use DiagnosticsToolbox to locate components.

## Solver options

Do not use `max_iter`, tolerances, or scaling options as the first fix. Confirm the installed option, connect it to observed evidence, offer it as one explicit change, and verify before/after results.

## Presentation rule

Use:

```text
Solver output:
[exact EXIT line, or structured status and termination]
What this means: [one short translation]
```

Never bury the final result in the full IPOPT table.
