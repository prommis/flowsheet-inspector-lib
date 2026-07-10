# Step Runner Guide

## Running the Full Flowsheet

Run the entire flowsheet in one go:
```bash
conda run -n [environment] python -c "
from [flowsheet_module] import FS
from idaes.core.util import DiagnosticsToolbox
FS.run_steps()
m = FS._context.model
dt = DiagnosticsToolbox(m)
dt.report_structural_issues()
dt.report_numerical_issues()
"
```

Capture all output. Never show the user the raw output directly.
Extract only the important lines as described below and format
them with plain English explanations.

## What to Show From IPOPT Output

Only show the EXIT message — nothing else. No constraint
violation, no iteration table, no other numbers.

Format:
"Solver output:
[EXIT message exactly as it appears in the output]
What this means: [plain English translation]"

EXIT message translations:
- "EXIT: Optimal Solution Found"
  What this means: The flowsheet solved successfully.
- "EXIT: Converged to a point of local infeasibility. Problem may be infeasible."
  What this means: The flowsheet did not solve.
- "EXIT: Maximum Number of Iterations Exceeded"
  What this means: The run ran out of attempts before finding
  a solution. Try fixing scaling issues first.
- "EXIT: Restoration Failed"
  What this means: The run failed badly. Check for model
  setup issues first.
- "EXIT: Error in AMPL Evaluation"
  What this means: A calculation failed — likely dividing by
  zero or using an invalid number.

## What to Show From DiagnosticsToolbox Output

Show each WARNING as a raw line followed immediately by a plain
English explanation on the next line. Never show CAUTION details
— just the count.

Format:
"Diagnostics output:
- [raw WARNING text exactly as it appears]
  What this means: [plain English translation]
- [raw WARNING text exactly as it appears]
  What this means: [plain English translation]

[X] minor cautions — fix the above first."

If 0 WARNINGs and 0 CAUTIONs:
"Diagnostics output:
No issues found."

WARNING translations:
- "Found X potential evaluation errors"
  What this means: Some calculations are using bad values like
  zero or numbers that are too big or too small.
- "X variable(s) at or outside bounds"
  What this means: A variable has gone outside its allowed range.
- "X constraint(s) with large residuals"
  What this means: Some equations are not being satisfied —
  this is caused by the other problems above, not a separate
  issue. Do not fix this directly — fix the root cause first.
- "Structural Singularity"
  What this means: The model has a conflict in its equations —
  too many constraints in one place and not enough in another.
- "Degrees of Freedom"
  What this means: The model has too many or too few fixed values.
- "X variable(s) with extreme values"
  What this means: Some variables have very large or very small
  values that make the run unstable.
- "Unit consistency"
  What this means: Two quantities with different units are being
  added or compared — like adding temperature to pressure.

## Never Fix Outside the Flowsheet File

The agent should only edit the flowsheet file the user provided.
Before attempting any fix, always check: can this be fixed by
editing the flowsheet file?

- Yes → fix it directly in the file and re-run diagnostics
- No → explain the issue in plain English, suggest what to
  look into, and give the final summary — do not attempt fixes
  outside the flowsheet file

Examples of fixes that CAN be made in the flowsheet file:
- changing a .fix() value that is outside bounds
- adding or removing a .fix() call to fix DOF
- deactivating a redundant constraint
- adding initialization for a unit model

Examples of fixes that CANNOT be made in the flowsheet file:
- property package internal expressions
  (e.g. eq_P_vap, eq_temperature_bubble, eq_temperature_dew)
- IDAES source code
- configuration files outside the flowsheet

When a fix cannot be made in the flowsheet file, tell the user:
"[WARNING text]: This is in the property package, not your
flowsheet file. I cannot fix this directly. Try solving anyway
— this may not prevent the flowsheet from running. If it still
fails, check the property package configuration or ask your
IDAES contact."
Then give the final summary.

## Running Suggested Next Steps

When the agent suggests a next step like dt.display_overconstrained_set():
- ask "Can I run [method name] to get more details?"
- STOP and wait for user response
- if yes: run it silently, show only the relevant output lines
  in the same format (raw line + What this means), explain in
  1-2 plain English sentences
- if no: ask user to run it themselves and paste the result
  and STOP — wait for them to paste before continuing

Before attempting any fix after running a next step:
- check whether the fix can be made in the flowsheet file
- if yes: fix it, re-run diagnostics, continue
- if no: explain and give the final summary

## Stopping Conditions

Stop diagnosing and give the final summary when any of these
are true. Do not continue past a stopping condition even if
there are more WARNINGs or CAUTIONs remaining.

**Success:**
EXIT: Optimal Solution Found AND 0 WARNINGs found.
Tell the user: "All done. Your flowsheet is working correctly."

**Same WARNING after 2 fix attempts:**
If the same WARNING appears after 2 rounds of fixes, tell the
user what is happening and ask if they want to continue:
"I have tried fixing [WARNING] twice but it is still showing.
This may need deeper investigation. Here is where things stand:
[summary of what was fixed and what remains]
Would you like me to keep trying, or shall I stop here and
give you a summary of what is left to look into?"

STOP and wait for user response.
- If yes: continue trying with a different approach
- If no: give the final summary

**Fix cannot be made in the flowsheet file:**
If fixing a WARNING requires changes outside the flowsheet file,
explain what it is and why it cannot be fixed, then give the
final summary. Do not keep diagnosing.

**CAUTIONs only remaining:**
Once all WARNINGs are resolved, do not automatically chase
CAUTIONs. Give the final summary. Only investigate CAUTIONs
if the user explicitly asks after the summary.

## Final Summary Format

Only show the final summary after hitting a stopping condition
or after all WARNINGs are resolved.

If everything passed:
"All done. Your flowsheet is working correctly."

If issues were found and fixed:
"All done. I found and fixed [issue] — your flowsheet is now
working correctly."

If issues remain that cannot be fixed in the flowsheet file:
"Your flowsheet still has an issue I cannot fix directly:
[issue in plain English]: [one line what to look into]
Try solving anyway — this may not prevent the flowsheet from
running. If it still fails, check with your IDAES contact."

If same WARNING appeared after 2 fix attempts and user said stop:
"This issue kept coming back after 2 fix attempts:
[WARNING]: [one line what to check manually]
Everything else looks good. Try solving and see what happens."
