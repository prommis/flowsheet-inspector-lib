# DiagnosticsToolbox Guide

Use the installed DiagnosticsToolbox report to explain what is wrong and choose one focused next step. Preserve the report's exact warning text, tolerance, and suggested method names.

## Standard sequence

For a completed model:

```python
from idaes.core.util import DiagnosticsToolbox

dt = DiagnosticsToolbox(model)
dt.report_structural_issues()
dt.report_numerical_issues()
```

For a partial model retained after a failed run:

```python
dt = DiagnosticsToolbox(model)
dt.report_structural_issues()
dt.display_variables_with_none_value_in_activated_constraints()
dt.display_variables_at_or_outside_bounds()
```

Label the focused results as partial-model evidence. Do not run the full numerical report on an unfinished model.

Use the normal review order: degrees of freedom, structural issues, unit consistency, bounds, then other numerical warnings. On a partial model, do not let broad structural artifacts outrank an explicit current violation that identifies a component, value, and bounds. After any model change, start again with the structural report.

## Severity

- **WARNING:** important issue to understand before trusting the run.
- **Caution:** condition worth checking, but it may be intentional and does not automatically block the flowsheet.

Show each warning. Show only the number of cautions unless the user asks to investigate them.

## Warning translations and next checks

### Degrees of Freedom is not zero

```text
What this means: The model has too many or too few fixed values or active equations.
Fix: Identify the unmatched variables or equations before solving.
```

- Positive DOF: inspect missing specifications or `.fix()` calls.
- Negative DOF: inspect extra `.fix()` calls or redundant constraints.
- Follow the report's suggested under/over-constrained-set method when present.

### Structural singularity

```text
What this means: Some equations conflict while other variables are not uniquely controlled.
Fix: Locate the over-constrained and under-constrained sets and correct the extra and missing relationships.
```

Typical focused methods, when named by the report and present in the installed API:

- `display_overconstrained_set()`
- `display_underconstrained_set()`

### Potential evaluation errors

```text
What this means: Some calculations can receive invalid values, such as division by zero or a logarithm of a nonpositive number.
Fix: Locate those expressions and check the values and bounds used by them.
```

Focused method: `display_potential_evaluation_errors()`.

### Variables at or outside bounds

```text
What this means: One or more variables are at or beyond their allowed range.
Fix: Identify the variables and correct an invalid fixed value, operating condition, or bound.
```

Focused method: `display_variables_at_or_outside_bounds()`.

When the focused output identifies a fixed variable outside its bounds:

- show the component name, current value, and allowed range;
- inspect the matching flowsheet specification;
- do not invent a replacement value;
- ask the user how they want to correct the specification.

Prioritize a fixed variable outside its bounds over a free variable merely sitting at a bound.

### Variables near bounds

```text
What this means: One or more variables are close to the edge of their allowed range.
Fix: Check whether the operating condition or bound is intentionally tight.
```

Focused method: `display_variables_near_bounds()`.

### Constraints with large residuals

```text
What this means: Some equations are not currently satisfied.
Fix: Check bounds, invalid evaluations, and structural warnings first; residuals are often a symptom.
```

Focused method: `display_constraints_with_large_residuals()`.

### Variables with extreme values

```text
What this means: Some variable values are much larger or smaller than the rest of the model.
Fix: Confirm the values are expected, then check or add appropriate scaling in the flowsheet.
```

Focused method: `display_variables_with_extreme_values()`.

### Poor scaling

```text
What this means: Some equations or variables operate on very different numerical scales.
Fix: Locate the affected components and set scaling from representative values.
```

Use the exact scaling method recommended by the installed report. Do not invent a universal scaling factor.

### Near-parallel or duplicate constraints

```text
What this means: Two equations may be providing nearly the same information.
Fix: Confirm whether one constraint is redundant before deactivating anything.
```

Focused method: `display_near_parallel_constraints()` when recommended and available.

### Unit consistency

```text
What this means: An expression combines quantities whose units are not compatible.
Fix: Locate the component and correct the units or conversion in the flowsheet code.
```

Use the exact installed method suggested by the report.

## Choosing one next step

Prefer the methods printed under the report's `Suggested next steps` or `Next Steps`.

For a completed model, use this priority:

1. over/under-constrained sets for structural singularity or nonzero DOF;
2. unit consistency;
3. variables at/outside bounds;
4. variables near bounds;
5. potential evaluation errors;
6. extreme values or scaling;
7. large residuals;
8. cautions only when the user asks.

For a partial model, use the direct bounds-check output ahead of broad structural follow-ups when it shows a fixed variable outside its bounds. Treat missing values, free variables at a bound, residuals, and potential evaluation errors as lower priority than that confirmed current violation.

Verify the exact method against the installed object:

```python
import inspect

method = getattr(dt, method_name, None)
signature = inspect.signature(method) if callable(method) else None
documentation = inspect.getdoc(method) if callable(method) else None
```

Do not select a fuzzy name. Run only an exact report-suggested method that can be called without unsupported required arguments.

## Focused output

For each relevant component line use:

```text
[raw component line]
What this means: [what the variable, constraint, or expression is doing]
Fix: [one precise check or change]
```

Do not claim a partial-initialization warning is the original root cause until the focused output and source specification confirm it.
