---
name: prommis-change-value
description: Finds and changes a .fix() parameter value in a PrOMMiS/IDAES flowsheet from a plain English instruction. TRIGGER when: user wants to change, set, adjust, or modify any operating condition or parameter value in a flowsheet. DO NOT TRIGGER when: user wants to wrap a flowsheet, understand a solver error, or find an import path.
compatibility: Requires the same conda environment as the flowsheet being modified — idaes-fi for flowsheets importing from prommis or idaes_fi, prommis-dev for flowsheets importing from idaes_examples.
metadata:
  author: Tanushree Subramanian
  version: "1.0"
---

# PrOMMiS Change Variable Value

PrOMMiS flowsheets set input parameters using `.fix()` calls. Finding
the right line yourself means digging through hundreds of lines of
code. This skill does that for you from a plain English instruction.
Works with both wrapped and unwrapped flowsheets.

## When to Use

Use this when you want to:
- change a flow rate, temperature, pressure, split fraction, or any
  other operating condition
- try out different parameter values
- adjust a feed composition or conversion target

## Core Concepts

**.fix()** — locks a variable to a specific value so IPOPT treats it
as a fixed input rather than solving for it.

**Parameter function** — the function where all input parameters get
set before solving. In wrapped flowsheets this is decorated as
@FS.step("set_operating_conditions") and may be called
set_operating_conditions. In unwrapped flowsheets it may have any
name — look for the function that contains .fix() calls on model
variables, such as set_inputs, set_params, set_conditions, or
similar. This is where changes happen.

**Units** — always read units directly from the .fix() call in the
code. If units are explicit (pyunits annotation), report them. If
units are implicit (bare number), infer from the variable name and
tell the user the units are assumed, not confirmed.

## Stage 1 — Understand the Request

Always announce: "Stage 1 — reading [filename]."

When the user names a file and describes what to change, read the
file directly from the workspace. Do not ask the user to paste code
or open the file.

Identify:
- which variable they want to change
- what the new value should be
- where the relevant .fix() call is in the file — check ALL
  functions, not just set_operating_conditions. In unwrapped
  flowsheets the function may have a different name like set_inputs,
  set_params, or set_conditions
- what the current value is
- what units the variable uses (from the code, not from assumptions)

After finding the .fix() call, always confirm units with the user
in one line before proceeding to stage 2:
"Units for this value are [units] — did you mean [new value][units]?"

Examples:
- "Units are Kelvin — did you mean 400K?"
- "Units are mol/s — did you mean 100 mol/s?"
- "Units assumed Kelvin (no annotation) — did you mean 400K?"

Wait for the user to confirm the units before proceeding to stage 2.

If the request is ambiguous — for example "change the flow rate" when
there are multiple flow rates in the file — ask which one before
the units confirmation:
"I found 3 flow rate .fix() calls:
- m.fs.H2.outlet.flow_mol[0].fix(637.2 * pyunits.mol / pyunits.s)
  in set_inputs
- m.fs.CO.outlet.flow_mol[0].fix(316.8 * pyunits.mol / pyunits.s)
  in set_inputs
- m.fs.M101.inlet.flow_mol[0].fix(100.0)
  in set_inputs
Which one do you want to change?"

## Stage 2 — Plan and Approve

Always announce: "Stage 2 — change plan."

Show the user exactly what will change before touching anything,
including which function the .fix() call is in:

Before:
```python
# in set_inputs
m.fs.flash.inlet.temperature.fix(368)
```
After:
```python
# in set_inputs
m.fs.flash.inlet.temperature.fix(400)
```

If the new value triggers any warning rule, warn before asking for
confirmation. See the warning rules below.

Always end with: "Confirm to apply this change?"

Wait for confirmation before making any change.

## Stage 3 — Apply and Confirm

Always announce: "Stage 3 — applying change."

Make only the specific .fix() line change that was approved directly
in the file. Do not ask the user to accept or reject — apply it
directly using file-write access.

Show only the changed line after applying — not the whole function.

Then confirm to the user:
"Done. [variable name] is now set to [human readable value and units
— e.g. '400K' not '400', '30 mol/s' not '30 * pyunits.mol / pyunits.s'].
Re-run the flowsheet to see the effect."

## Warning Rules

### Step 1: Read units from the code first
When you find the .fix() call, check whether units are explicit:
- explicit units (pyunits): report them directly to the user
  e.g. "Units are mol/s per pyunits annotation"
- implicit units (bare number, no pyunits): infer from the variable
  name and tell the user the units are assumed, not confirmed
  e.g. "Units assumed Kelvin (no annotation)"

### Step 2: Apply these general warning triggers
Warn the user before confirming when any of these are true:

- new value is more than 10x larger or smaller than the current
  value — likely a unit mismatch or typo
- new value is negative for a variable whose name contains: flow,
  mol, pressure, temperature, conversion, recovery, fraction —
  these are almost always positive quantities
- new value is outside 0 to 1 for a variable whose name contains:
  conversion, recovery, fraction, split, efficiency —
  these are dimensionless ratios
- new value has no pyunits annotation but the current value does —
  flag that the user may need to include units in the new value too

### Step 3: Warning format
"⚠️ [what triggered the warning]. Current value is [current]
[units]. Did you mean [interpreted value in human readable units]?
Confirm to proceed or give me a different value."

### Step 4: No warning needed when
- new value is within 10x of the current value
- new value is physically reasonable for the variable name
- units are explicit and the new value matches those units

## Output Rules

Never show the user:
- internal file reading operations
- reasoning about which function contains the .fix() call
- intermediate search steps
- any internal logic about unit detection or warning evaluation

Only show the user:
- the stage announcements
- the one line units confirmation
- any ambiguity questions
- the before and after lines in stage 2
- the warning if triggered
- the confirmation message in stage 3

Keep all internal reasoning and file operations invisible to
the user. The user should only see clean stage-by-stage output.

## Rules

- never change any flowsheet logic
- only change the specific .fix() value asked for
- always confirm units with the user in one line before showing
  the change plan
- always show before and after the specific line before applying,
  including which function it is in
- never change more than one .fix() call per request unless the user
  explicitly asks for multiple changes
- search ALL functions in the file for the .fix() call — do not
  restrict search to set_operating_conditions only
- if the variable cannot be found with a .fix() call anywhere in
  the file, say so and stop
- always show only the changed line after applying, never the whole
  function
- always apply changes directly to the file — never ask the user to
  accept or reject manually

## DO NOT Rules

- do not change any line other than the specific .fix() call asked for
- do not change function signatures, decorators, or imports
- do not add new .fix() calls that weren't already there
- do not remove existing .fix() calls
- do not change the value if the user has not confirmed
- do not apply a change that would set a value outside physically
  reasonable bounds without warning the user first
- do not paste the entire flowsheet or function back to the user —
  show only the changed line
- do not ask the user to open a diff UI or accept/reject anything —
  apply the change directly
- do not restrict the search to set_operating_conditions only —
  check all functions in the file
- do not proceed to stage 2 before the user has confirmed the units

## Common Pitfalls

- units mismatch: always confirm units with the user in one line
  after finding the .fix() call — never assume they know the units
- wrong variable: "change the flow rate" when multiple flow rates
  exist — always ask which one before proceeding
- wrong function name: in unwrapped flowsheets the parameter function
  may be called set_inputs, set_params, set_conditions, or anything
  else — always search all functions, never assume the name
- missing pyunits in new value: if the current .fix() call uses
  pyunits (e.g. fix(368 * pyunits.K)) and the user gives a bare
  number, flag that they may need to include the units annotation
  in the new value too
- ugly pyunits in confirmation message: always convert pyunits
  expressions to human readable form in the confirmation message
  e.g. say "30 mol/s" not "30 * pyunits.mol / pyunits.s"

## Deviation Handling

If the user gives a vague instruction like "change the temperature":
ask which temperature before showing any plan.

If the user gives a value without units and the current value has
explicit pyunits: include the units note in the one-line units
confirmation before applying.

If the user wants to change multiple values at once:
handle them one at a time, confirming units and showing a plan
for each one separately.

If the variable cannot be found anywhere in the file:
tell the user exactly what was searched for and where, and suggest
they check the variable name.

## Example Conversations

User: "change the flash inlet temperature to 400 in flash_flowsheet.py"

AI: "Stage 1 — reading flash_flowsheet.py.
Found: m.fs.flash.inlet.temperature.fix(368) in set_operating_conditions.
Units assumed Kelvin (no annotation) — did you mean 400K?"

User: "yes"

AI: "Stage 2 — change plan.
Before:
m.fs.flash.inlet.temperature.fix(368)
After:
m.fs.flash.inlet.temperature.fix(400)
Confirm to apply this change?"

User: "yes"

AI: "Stage 3 — applying change.
Done. Flash inlet temperature is now set to 400K.
Re-run the flowsheet to see the effect."

---

User: "set the CO flow to 100 in methanol_flowsheet.py"

AI: "Stage 1 — reading methanol_flowsheet.py.
Found: m.fs.CO.outlet.flow_mol[0].fix(316.8 * pyunits.mol / pyunits.s)
in set_inputs.
Units are mol/s — did you mean 100 mol/s?"

User: "yes"

AI: "Stage 2 — change plan.
Before:
m.fs.CO.outlet.flow_mol[0].fix(316.8 * pyunits.mol / pyunits.s)
After:
m.fs.CO.outlet.flow_mol[0].fix(100 * pyunits.mol / pyunits.s)
Confirm to apply this change?"

User: "yes"

AI: "Stage 3 — applying change.
Done. CO flow is now set to 100 mol/s.
Re-run the flowsheet to see the effect."