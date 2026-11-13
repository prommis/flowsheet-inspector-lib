---
title: API
---
# API

This section describes the application programming interface (API) used to
"wrap" flowsheets with the Flowsheet Inspector (FI).

To learn this API by example, skip down to the [Minimal Wrapper](#minimal-wrapper) section.

## Overview

FI instruments an ordinary IDAES flowsheet by placing its build, setup, initialization, and solve operations inside named steps. A wrapped flowsheet has three parts:

1. A `FlowsheetRunner` instance (here called `runner`), usually created at module scope.
2. A `main(runner)` function that performs the flowsheet work. After the required first
   argument, which is the `FlowsheetRunner` instance, any additional arguments can be used.
3. Calls to `runner.step_begin()` and, optionally, `runner.step_end()` around flowsheet
   operations.

### FlowsheetRunner object

The `FlowsheetRunner` object is the focus of the API. It is usually constructed at module scope.

#### Constructor 

`class FlowsheetRunner(steps: list[str] = None, flowsheet_block: str = "fs", report_db: Optional[bool | str | Path | ReportDB] = True, quiet: bool = False)`  
<dl class="args">
<dt>steps</dt><dd>List of steps in flowsheet. This can be any list of strings, but it is recommended to use the standard step names defined in <tt>idaes_fi.common.Steps</tt>. This argument is required.</dd>
<dt>flowsheet_block</dt><dd>Name in model of flowsheet block</dd>
<dt>report_db</dt><dd>If True or None, get default DB. If False, do not
                use a report db. Otherwise, use value as the report
                database (must be a filename or ReportDB instance).
<dt>quiet</dt><dd>If True, do not print anything to the console (logging
            may still occur, but that is controlled separately)
</dl>

#### Properties

Key behaviors of the `FlowsheetRunner` object are controlled by setting properties. 
* The following properties are required or recommended to set:
    * **main** _(required)_. This is a reference to the function mentioned above in (2), which takes the `FlowsheetRunner` instance as its first argument and runs the flowsheet. This function can take any additional position or keyword arguments. This should be assigned before the call to `run_flowsheet()`, typically at module scope right after the main function is defined.
    * **model** _(required, but not before running)_. The value of the Pyomo model must be assigned to this attribute in `FlowsheetRunner.main` during the first step of the flowsheet (typically called "build" or using the constant `Steps.build`). This allows for actions triggered at the end of each step to inspect and report on the state of the model.
    * **solve_result** _(recommended)_. Set this property to the return value of the Pyomo/IDAES `solver.solve()` call. If this is done, the solve result will be automatically extracted and visible in the Flowsheet Inspector interface. This property can be set multiple times in a single step (internally, it is stored as a list), and set in multiple steps (each step's solves are stored separately), so in other words it can be set any time a solve occurs in the code.
* The following properties are optional or read-only:
    * **last_step** _(optional)_. The name of the last step to run. If not set, every step is run. If set, after the step matching the given name, execution of the `FlowsheetRunner.main` function will stop.
    * **report_db_file** _(read-only)_. The SQLite file where the database used for tracking status and results -- the 'report' database -- is located. The default location can be changed (or even disabled) with the `report_db` argument passed to the `FlowsheetRunner` constructor. If the report database is disabled, this will be `None`.

#### Usage

The runner passes itself to the first argument of the `main`. Assign the constructed Pyomo model to `runner.model` during the build step so FI's reporting actions can inspect it. The value returned by `main` is returned by `runner.run_flowsheet()`.

## Minimal wrapper

The following is the basic pattern for an IDAES flowsheet module. The model
construction and solver code are ordinary IDAES/Pyomo code; only the runner
and step calls are FI-specific.

```{code} python
from pyomo.environ import ConcreteModel
from idaes.core import FlowsheetBlock
from idaes.core.solvers import get_solver

from idaes_fi import FlowsheetRunner, Steps

#--------------------------------------
# Create FlowsheetRunner object
#--------------------------------------

runner = FlowsheetRunner(steps=[
    Steps.build,
    Steps.initialize,
    Steps.set_solver,
    Steps.solve_optimization,
])

#--------------------------------------
# Existing code to build, solve, etc.
# the flowsheet does not change
#--------------------------------------

def build_flowsheet():
    model = ConcreteModel()
    model.fs = FlowsheetBlock(dynamic=False)
    # Add the property package, unit models, arcs, and constraints here.
    return model

# initialize, solve, etc..

#--------------------------------------
# Add step_begin/end and set model
# in main function.
#--------------------------------------

def main(runner):
    runner.step_begin(Steps.build)
    runner.model = model = build_flowsheet()

    runner.step_begin(Steps.initialize)
    # Initialize units as required by the flowsheet.

    runner.step_begin(Steps.set_solver)
    solver = get_solver()

    runner.step_begin(Steps.solve_optimization)
    solver.solve(model, tee=True)

    return model

#--------------------------------------
# Run the flowsheet
#--------------------------------------

runner.main = main

if __name__ == "__main__":
    model = runner.run_flowsheet()
```


### Step begin/end

`step_begin()` closes the previous open step automatically. FI also closes the last open step when `run_flowsheet()` finishes, so explicit `step_end()` calls are needed only when some code should be executed that is not part of any step. For example, the scaling step in the test flowsheet is explicitly closed so that the `set_degrees_of_freedom()` function is not inside either th scaling step or the subsequent initialization step:

```{code} python
runner.step_begin(Steps.set_scaling)
set_scaling(model)
runner.step_end()

set_degrees_of_freedom(model)
runner.step_begin(Steps.initialize)
initialize_flowsheet(model)
```

## Running a wrapped module

Run a module directly from Python with:

```{code} python
from my_flowsheet import runner

model = runner.run_flowsheet()
```

Alternatively, use the API loader. It accepts either an importable module name or a filesystem path:

```{code} python
from pathlib import Path
from idaes_fi.api import run_flowsheet

run_flowsheet(module_name="my_flowsheet")
run_flowsheet(path=Path("my_flowsheet.py"))
```

`run_flowsheet()` discovers `FlowsheetRunner` instances in the loaded module. If the module contains one runner, it is selected automatically. If it contains multiple runners, pass `flowsheet_name` with the runner variable's
name, for example `flowsheet_name="FS2"`.

```{code} python
run_flowsheet(path=Path("flowsheets.py"), flowsheet_name="FS2")
```

The `flowsheet_block` argument to the `FlowsheetRunner` constructor names the flowsheet block in the Pyomo model and is
used by FI actions such as degree-of-freedom checks. It defaults to `"fs"`.

## Steps

Use the constants in `Steps` instead of spelling step names manually. The
available names include:

```{code} python
Steps.build
Steps.set_solver
Steps.initialize
Steps.set_operating_conditions
Steps.set_scaling
Steps.solve_initial
Steps.set_autoscaling
Steps.add_costing
Steps.initialize_costing
Steps.setup_optimization
Steps.solve_optimization
```

The `runner.steps` list records the steps used by the flowsheet and lets FI
actions interpret the run. It does not execute those steps.

## Reports and console output

By default, `FlowsheetRunner` writes FI action reports to the IDAES report
database. Use `report_db=False` to disable database reporting. When database
reporting is disabled, `quiet=False` prints the captured solver output and
errors at the end of the run; `quiet=True` suppresses that report.

To use a specific database, pass a `ReportDB` instance or path object/string from which to construct one:

```{code} python
from pathlib import Path
from idaes_fi import FlowsheetRunner
from idaes_fi.api import ReportDB

runner = FlowsheetRunner(
    report_db="reports.sqlite"
    # Equivalent: report_db=ReportDB(Path("reports.sqlite"))
)
```

The default action set collects solver output, diagnostics, unit-model and
variable reports, stream tables, timings, a Mermaid diagram, and the Git hash
when available. The runner's `report_db_file` property identifies the active
database when database reporting is enabled.
