# DiagnosticsToolbox Guide

## Note on Method Names

The DiagnosticsToolbox method names listed in this guide are based
on idaes 2.12.0. Before suggesting any method to the user, run
this silently to verify the method exists in the installed version:

```bash
conda run -n [environment] python -c "
from idaes.core.util import DiagnosticsToolbox
methods = [m for m in dir(DiagnosticsToolbox) if not m.startswith('_')]
print('\n'.join(methods))
"
```

Run this silently. If a method name in this guide does not appear
in the output, find the closest matching method name from the output
and use that instead. Never suggest a method that does not exist in
the installed version.

## What DiagnosticsToolbox Does

DiagnosticsToolbox checks your flowsheet for problems that would
cause it to fail to solve or give wrong results. It has two phases.

Phase 1 — structural checks, run BEFORE solving:

    dt = DiagnosticsToolbox(m)
    dt.report_structural_issues()

Phase 2 — numerical checks, run AFTER solving:

    dt.report_numerical_issues()

Always fix structural issues before numerical issues.
Always re-run report_structural_issues() after any change to the model.

## How to Read the Output

Two severity levels:

WARNING — must fix before the model will solve correctly
CAUTION — worth investigating but model may still solve

## Structural Issues and Fixes

### DOF is not zero

What it means: DOF = variables minus equations. DOF > 0 means not
enough .fix() calls. DOF < 0 means too many .fix() calls or a
duplicate constraint.

How to fix DOF > 0: add .fix() calls in set_operating_conditions.
How to fix DOF < 0: remove a .fix() call or deactivate a constraint.

### Structural singularity

What it means: the model has an over-constrained set and an
under-constrained set at the same time. Some variables can never
be determined even if DOF = 0.

How to find it — verify these method names exist before suggesting:

    dt.display_overconstrained_set()
    dt.display_underconstrained_set()

How to fix: check the over-constrained set for a redundant
constraint or extra .fix() call. Check the under-constrained set
for a missing .fix() call or missing equation.

### Unit consistency issue

What it means: a constraint mixes incompatible units, like adding
Kelvin to Pascal. Will always give wrong results even if it solves.

How to find it — verify method name exists before suggesting:

    dt.display_components_with_inconsistent_units()

How to fix: find the constraint shown and fix the units. Usually
a missing unit conversion or wrong property package.

## Numerical Issues and Fixes

### Variable at or outside bounds

What it means: a variable has hit or exceeded its bound. The most
common cause of a failed run. The calculation cannot move past a bound.

How to find it — verify method name exists before suggesting:

    dt.display_variables_at_or_outside_bounds()

How to fix: relax the bound if too tight, or check if operating
conditions are outside the valid range for the property package.

### Variable near bounds

What it means: a variable is close to but not yet at its bound.
Warning sign that infeasibility may be coming.

How to find it — verify method name exists before suggesting:

    dt.display_variables_near_bounds()

How to fix: same as above.

### Constraint with large residual

What it means: a constraint is not being satisfied. This is usually
a symptom, not the root cause. Always check bounds violations first.

How to find it — verify method name exists before suggesting:

    dt.display_constraints_with_large_residuals()

How to fix: do not fix the constraint directly. Find the root cause
first — usually a variable outside its bounds or a scaling issue.

### Variable with extreme value

What it means: a variable has a very large or very small value like
1e10 or 1e-10. Causes numerical precision problems during the run.

How to find it — verify method name exists before suggesting:

    dt.display_variables_with_extreme_values()

How to fix: set a scaling factor for that variable:

    iscale.set_scaling_factor(m.fs.unit.variable, 1/typical_value)
    iscale.calculate_scaling_factors(m)

### Near parallel constraints

What it means: two constraints are nearly identical — one is
redundant. Causes degeneracy, which can make the run struggle.

How to find it — verify method name exists before suggesting:

    dt.display_near_parallel_constraints()

How to fix: deactivate one of the redundant constraints.

## Degeneracy

Degeneracy means one or more constraints are redundant. Signs:
- the run takes many more iterations than expected
- ls column in IPOPT log consistently greater than 1
- SVD analysis shows near-zero singular values

How to check for degeneracy — verify method names exist before
suggesting:

    svd = dt.prepare_svd_toolbox()
    svd.display_rank_of_equality_constraints()

Each near-zero singular value means one degenerate constraint.

How to find the exact redundant constraints — verify method names
exist before suggesting:

    dh = dt.prepare_degeneracy_hunter()
    dh.report_irreducible_degenerate_sets()

Note: degeneracy hunter requires SCIP solver.

## Debugging Order

Always follow this order:

1. Run report_structural_issues()
2. Fix all WARNINGs
3. Fix CAUTIONs if needed
4. Re-run report_structural_issues() to confirm fixed
5. Try to solve
6. Run report_numerical_issues()
7. Fix WARNINGs — check bounds violations before residuals
8. Fix CAUTIONs
9. Re-solve and verify

## Import

    from idaes.core.util import DiagnosticsToolbox
    dt = DiagnosticsToolbox(m)
