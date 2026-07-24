# Wrapping Examples

## Contents

- [Example conversation](#example-conversation)
- [Function-by-function mode](#function-by-function-mode)
- [One-shot mode](#one-shot-mode)
- [Original flash flowsheet](#flash-flowsheet--before-original-unwrapped-version)
- [Wrapped flash flowsheet](#flash-flowsheet--after-wrapped-version)
- [Summary of changes](#what-changed)

## Example Conversation

This is what a complete wrapping conversation should look like.
Copied flowsheet code stays formatted like the original except for
the permitted wrapper transformations described in `SKILL.md`.

### Function-by-Function Mode

User: "wrap flash_flowsheet.py"

AI: "Stage 1 reading flash_flowsheet.py.

I found 4 functions. It has initialization, no costing, and no
optimization objective. The original execution order is build_model,
set_operating_conditions, init_model, solve. The required environment
is idaes-fi."

AI: "Stage 2 wrapping plan.

| # | Plan item | Wrapped result |
|---|-----------|----------------|
| 1 | imports and runner setup | add FlowsheetRunner, Context, and the explicit ordered steps sequence |
| 2 | build_model | `@FS.step('build')` |
| 3 | set_solver | add wrapper-only `@FS.step('set_solver')` |
| 4 | set_operating_conditions | `@FS.step('set_operating_conditions')` |
| 5 | init_model | `@FS.step('initialize')` |
| 6 | solve | `@FS.step('solve_initial')` |
| 7 | __main__ block | `FS.run_steps()` |

Execution order: build, set_solver, set_operating_conditions,
initialize, solve_initial

Total plan items: 7

Wrapping modes:
1. Function-by-function: show, confirm, and write each item.
2. One-shot: write the complete approved plan, then verify it.

Confirm this plan and choose a mode."

User: "Plan confirmed. Use function-by-function mode."

AI: "What would you like to name the wrapped file? Default is
flash_flowsheet_wrapped.py"

User: "flash_flowsheet_wrapped.py"

AI: "Stage 2 wrapping in progress.

Imports and runner setup:
[shows original imports plus FlowsheetRunner, Context, and the
approved explicit steps sequence]

Confirm to write this item."

User: "Confirmed."

AI: "build_model wrapped as `@FS.step('build')`:
[shows only the wrapped build_model item]

Confirm to write this item."

User: "Confirmed."

AI: "Wrapper-only `@FS.step('set_solver')`:
[shows only set_solver]

Confirm to write this item."

[continues one item at a time through the remaining functions and the
`__main__` block; each item is written only after confirmation]

AI: "Stage 3 running verification checklist.

- Mode-Specific Writing Gate: PASS
- Plan Completeness Check: PASS
- Valid Step Name Check: PASS
- Execution Order Check: PASS
- Source Accounting Check: PASS
- Normalized Source Preservation Check: PASS
- Import Check: PASS
- Context Check: PASS
- Bottom of File Check: PASS
- Syntax Check: PASS
- Confirm File Written: PASS

Written to flowsheet/flash_flowsheet_wrapped.py.
Activate the required environment before running it:
conda activate idaes-fi"

### One-Shot Mode

The one-shot conversation uses the same Stage 1 findings and Stage 2
plan shown above.

User: "Plan confirmed. Use one-shot mode."

AI: "What would you like to name the wrapped file? Default is
flash_flowsheet_wrapped.py"

User: "flash_flowsheet_wrapped.py"

AI: "Stage 2 wrapping in progress."

[writes all seven approved plan items to the new file in one pass;
does not show or request confirmation for individual items]

AI: "Stage 3 running verification checklist.

- Mode-Specific Writing Gate: PASS
- Plan Completeness Check: PASS
- Valid Step Name Check: PASS
- Execution Order Check: PASS
- Source Accounting Check: PASS
- Normalized Source Preservation Check: PASS
- Import Check: PASS
- Context Check: PASS
- Bottom of File Check: PASS
- Syntax Check: PASS
- Confirm File Written: PASS

Written to flowsheet/flash_flowsheet_wrapped.py.
Activate the required environment before running it:
conda activate idaes-fi"

## Flash Flowsheet — Before (original unwrapped version)

```python
from pyomo.environ import ConcreteModel, SolverFactory
from pyomo.network import Arc, Port
from pyomo.core import TransformationFactory
from idaes.core import FlowsheetBlock
import idaes.logger as idaeslog
from idaes.models.properties.activity_coeff_models.BTX_activity_coeff_VLE import (
    BTXParameterBlock,
)
from idaes.models.unit_models import Flash, Valve

def build_model():
    m = ConcreteModel()
    m.fs = FlowsheetBlock(dynamic=False)
    m.fs.properties = BTXParameterBlock(
        valid_phase=("Liq", "Vap"), activity_coeff_model="Ideal", state_vars="FTPz"
    )
    m.fs.flash = Flash(property_package=m.fs.properties)
    m.fs.valve = Valve(property_package=m.fs.properties)
    m.fs.flash_to_valve = Arc(
        source=m.fs.flash.vap_outlet, destination=m.fs.valve.inlet
    )
    TransformationFactory("network.expand_arcs").apply_to(m)
    m.fs.vap_outlet = Port(extends=m.fs.flash.vap_outlet)
    m.fs.liq_outlet = Port(extends=m.fs.flash.liq_outlet)
    m.fs.valve_outlet = Port(extends=m.fs.valve.outlet)
    return m

def set_operating_conditions(m):
    m.fs.flash.inlet.flow_mol.fix(1)
    m.fs.flash.inlet.temperature.fix(368)
    m.fs.flash.inlet.pressure.fix(101325)
    m.fs.flash.inlet.mole_frac_comp[0, "benzene"].fix(0.5)
    m.fs.flash.inlet.mole_frac_comp[0, "toluene"].fix(0.5)
    m.fs.flash.heat_duty.fix(0)
    m.fs.flash.deltaP.fix(0)

def init_model(m):
    m.fs.flash.initialize(outlvl=idaeslog.INFO)

def solve(m):
    solver = SolverFactory("ipopt")
    solver.solve(m, tee=True)

if __name__ == "__main__":
    m = build_model()
    set_operating_conditions(m)
    init_model(m)
    solve(m)
```

## Flash Flowsheet — After (wrapped version)

```python
from pyomo.environ import ConcreteModel, SolverFactory
from pyomo.network import Arc, Port
from pyomo.core import TransformationFactory
from idaes.core import FlowsheetBlock
import idaes.logger as idaeslog
from idaes.models.properties.activity_coeff_models.BTX_activity_coeff_VLE import (
    BTXParameterBlock,
)
from idaes.models.unit_models import Flash, Valve
from idaes_fi.structfs.fsrunner import FlowsheetRunner, Context

FS = FlowsheetRunner(
    steps=(
        "build",
        "set_solver",
        "set_operating_conditions",
        "initialize",
        "solve_initial",
    )
)

@FS.step("build")
def build_model(ctx: Context):
    m = ConcreteModel()
    m.fs = FlowsheetBlock(dynamic=False)
    m.fs.properties = BTXParameterBlock(
        valid_phase=("Liq", "Vap"), activity_coeff_model="Ideal", state_vars="FTPz"
    )
    m.fs.flash = Flash(property_package=m.fs.properties)
    m.fs.valve = Valve(property_package=m.fs.properties)
    m.fs.flash_to_valve = Arc(
        source=m.fs.flash.vap_outlet, destination=m.fs.valve.inlet
    )
    TransformationFactory("network.expand_arcs").apply_to(m)
    m.fs.vap_outlet = Port(extends=m.fs.flash.vap_outlet)
    m.fs.liq_outlet = Port(extends=m.fs.flash.liq_outlet)
    m.fs.valve_outlet = Port(extends=m.fs.valve.outlet)
    ctx.model = m

@FS.step("set_solver")
def set_solver(ctx: Context):
    ctx.solver = SolverFactory("ipopt")

@FS.step("set_operating_conditions")
def set_operating_conditions(ctx: Context):
    m = ctx.model
    m.fs.flash.inlet.flow_mol.fix(1)
    m.fs.flash.inlet.temperature.fix(368)
    m.fs.flash.inlet.pressure.fix(101325)
    m.fs.flash.inlet.mole_frac_comp[0, "benzene"].fix(0.5)
    m.fs.flash.inlet.mole_frac_comp[0, "toluene"].fix(0.5)
    m.fs.flash.heat_duty.fix(0)
    m.fs.flash.deltaP.fix(0)

@FS.step("initialize")
def init_model(ctx: Context):
    m = ctx.model
    m.fs.flash.initialize(outlvl=idaeslog.INFO)

@FS.step("solve_initial")
def solve(ctx: Context):
    m = ctx.model
    ctx["results"] = ctx.solver.solve(m, tee=ctx["tee"])

if __name__ == "__main__":
    FS.run_steps()
```

## What Changed

- added `from idaes_fi.structfs.fsrunner import FlowsheetRunner, Context`
- derived `build`, `set_operating_conditions`, `initialize`, and
  `solve_initial` order from the original `__main__` block
- inserted the wrapper-only `set_solver` immediately after `build`
- added the resulting explicit sequence with
  `FS = FlowsheetRunner(steps=(...))`
- added decorators and context handling without changing the copied
  flowsheet logic
