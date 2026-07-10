# Wrapping Examples

## Example Conversation

This is what a full wrapping conversation should look like.

User: "wrap flash_flowsheet.py"

AI: "I found 4 functions in flash_flowsheet.py. Here is my wrapping plan:
- build_model -> @FS.step("build")
- set_operating_conditions -> @FS.step("set_operating_conditions")
- init_model -> @FS.step("initialize")
- solve -> @FS.step("solve_initial")
- adding new set_solver step
- adding explicit steps= order to FlowsheetRunner since this flowsheet
  fixes inputs in set_operating_conditions and must initialize after,
  not before
Confirm to proceed?"

User: "yes"

AI: "What would you like to name the wrapped file? Default is
flash_flowsheet_wrapped.py"

User: "flash_flowsheet_wrapped.py"

AI: "Creating flowsheet/flash_flowsheet_wrapped.py. I will show one item
at a time and only write each item after you confirm it.

Wrapping build_model — here is the complete wrapped function:
[shows just build_model wrapped]
Does this look right? Confirm to continue to set_operating_conditions."

User: "looks good"

AI: "Wrapping set_operating_conditions — here is the complete wrapped
function: [shows just set_operating_conditions wrapped]
Does this look right? Confirm to continue."

[continues function by function until all done, including the steps=
ordering tuple and the __main__ block as their own confirmed items]

AI: "All items wrapped and confirmed. Running diff check:
- function count: original 4, wrapped 5 (1 new set_solver) ✓
- no lines dropped ✓
- imports correct ✓
- context handling correct ✓
- step names all valid ✓
- steps= ordering present and correct ✓"

AI: "Written to flowsheet/flash_flowsheet_wrapped.py.
Activate idaes-fi before running it:
conda activate idaes-fi
If a step fails during a run you may see an AttributeError mentioning
_solver_out — this is a known idaes-fi library bug, the real issue
is whatever step actually failed."

## Why steps= Ordering Matters

FlowsheetRunner does not run steps in the order they appear in the
file. It uses an internal default canonical order that runs
initialize BEFORE set_operating_conditions, which breaks any
flowsheet that fixes inputs before initializing — the normal case.

Always pass an explicit steps= tuple to FlowsheetRunner() when the
flowsheet has both an initialize step and a set_operating_conditions
step:

```python
FS = FlowsheetRunner(
    steps=(
        "build",
        "set_solver",
        "set_operating_conditions",
        "set_scaling",
        "initialize",
        "solve_initial",
    )
)
```

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

@FS.step("set_solver")
def set_solver(ctx: Context):
    ctx.solver = SolverFactory("ipopt")

@FS.step("solve_initial")
def solve(ctx: Context):
    ctx["results"] = ctx.solver.solve(ctx.model, tee=ctx["tee"])

if __name__ == "__main__":
    FS.run_steps()
```

## What Changed

- added `from idaes_fi.structfs.fsrunner import FlowsheetRunner, Context`
- added `FS = FlowsheetRunner(steps=(...))` with explicit ordering so
  set_operating_conditions and initialize run before set_solver and
  solve_initial in the correct sequence
- added `@FS.step("build")` above build_model
- changed `build_model()` -> `build_model(ctx: Context)`
- replaced `return m` -> `ctx.model = m`
- added `@FS.step("set_operating_conditions")` above set_operating_conditions
- changed all `(m)` -> `(ctx: Context)`
- added `m = ctx.model` as first line of each step except build
- added separate `@FS.step("set_solver")` step
- replaced `SolverFactory("ipopt")` + `solver.solve()` in solve ->
  `ctx.solver.solve(ctx.model, tee=ctx["tee"])`
- replaced `tee=True` -> `tee=ctx["tee"]`
- replaced manual calls at bottom -> `FS.run_steps()`

## Note on Complex Flowsheets

For a more complex wrapping example including the substep pattern
(@FS.substep) and a real-world steps= ordering tuple, open
hda_flowsheet.py or methanol_flowsheet.py from the flowsheet/ folder
in the flowsheet-inspector repo.

Substeps are used when helper functions inside build need to be visible
to the Flowsheet Inspector. If they are just internal helpers, leave
them as plain functions called from inside build.code 
