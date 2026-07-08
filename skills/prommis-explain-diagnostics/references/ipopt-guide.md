# IPOPT Output Guide

## Note on IPOPT Version

The column names and exit messages in this guide are based on
IPOPT 3.14. Before explaining any specific column or message,
run this silently to check the installed IPOPT version:

```bash
conda run -n [environment] python -c "
from idaes.core.solvers import get_solver
solver = get_solver()
print(solver.version())
"
```

If the version differs significantly from 3.14, the column names
and exit messages in this guide may differ slightly. Use the
guide as a conceptual reference and adapt explanation to what
the user actually pasted.

## What IPOPT Output Looks Like

When you run solver.solve(m, tee=True) you see the full IPOPT log.
Here is what each section means.

## Header Section

    Number of variables: 4
    Number of equality constraints: 4
    Number of inequality constraints: 0

Variables should equal equality constraints for a square model
(DOF = 0). If they do not match, check DOF before solving.

## Iteration Table Columns

iter — iteration number

objective — current objective value

inf_pr — constraint violation. Must reach near 1e-8 for success.
         If stuck at the same value across many iterations, a
         variable has hit a bound.

inf_du — dual infeasibility. Must also reach near 1e-8.

lg(mu) — barrier parameter. Decreases as IPOPT converges.

lg(rg) — regularization coefficient. If this has persistent values
          across many iterations, the Jacobian is singular.
          Structural problem — run report_structural_issues().

alpha_pr — step size for primal variables. If consistently very
           small like 1e-8, IPOPT is struggling.

ls — line search steps. If consistently greater than 1, IPOPT is
     struggling to make progress. Sign of degeneracy or poor scaling.

## Warning Signs in the Iteration Table

inf_pr stuck at same value for many iterations:
A variable has hit a bound. Run display_variables_at_or_outside_bounds()
— verify this method name exists in the installed version first.

r appearing next to iteration number:
IPOPT entered restoration phase. Very bad sign. Run
report_structural_issues() before trying again.

lg(rg) column has persistent values with L or l tags:
Jacobian is singular. Run report_structural_issues().

ls consistently greater than 10:
Degeneracy or very poor scaling. Run prepare_svd_toolbox() —
verify this method name exists in the installed version first.

alpha_pr very small consistently:
Variable near a bound or model poorly scaled.

## EXIT Messages

### EXIT: Optimal Solution Found

Solve succeeded. inf_pr and inf_du both reached near zero.
Check that solution values are physically reasonable.

### EXIT: Converged to a point of local infeasibility. Problem may be infeasible.

IPOPT could not satisfy all constraints. Most common causes:
- variable outside its bounds
  run: display_variables_at_or_outside_bounds()
- structural singularity
  run: report_structural_issues()
- operating conditions outside valid range for property package

Always verify method names exist in the installed version before
suggesting them to the user.

### EXIT: Maximum Number of Iterations Exceeded

Hit the iteration limit. Not necessarily infeasible — may just
need more iterations or better scaling.

Try: solver.options['max_iter'] = 5000
Or check scaling: run display_variables_with_extreme_values() —
verify this method name exists in the installed version first.

### EXIT: Restoration Failed

Restoration phase also failed. Model is very poorly conditioned.
Run report_structural_issues() and fix all structural issues
before trying again.

### EXIT: Error in AMPL Evaluation

A constraint or objective evaluation failed — usually division
by zero or log of a negative number. Check initial values and
bounds for variables in nonlinear expressions.

## Summary Section

At the end of the log:

    Constraint violation = 8.40e+02
    Overall NLP error    = 8.40e+02

If constraint violation is above 1e-4, the model did not solve
even if IPOPT said it converged. Always check this number.

## Debugging Order for IPOPT Failures

1. Read the EXIT message first
2. If infeasible: run report_structural_issues() and
   display_variables_at_or_outside_bounds()
3. If max iterations: check scaling first, then increase limit
4. If restoration failed: run report_structural_issues()
5. If error in evaluation: check initial values and bounds
6. Never try to fix IPOPT output directly without running
   DiagnosticsToolbox first — IPOPT symptoms are caused by
   structural or scaling issues that DiagnosticsToolbox catches

## Important

Always run the method name verification silently before suggesting
any DiagnosticsToolbox method to the user. Never suggest a method
that does not exist in the installed version. If a method name has
changed, find the closest match from the actual installed class and
suggest that instead.