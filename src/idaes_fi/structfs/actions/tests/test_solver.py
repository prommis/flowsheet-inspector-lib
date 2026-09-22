"""
Test for the solver action.
"""

from idaes_fi.structfs import FlowsheetRunner, Steps
from idaes_fi.structfs.common import ActionNames
from idaes_fi.structfs.tests.demo_flowsheet import *

import pytest

_solver_name = "couenne"

##############################
# Create a wrapped flowsheet #
##############################

FS = FlowsheetRunner(
    name="Demo Flowsheet with Couenne",
    tags="test demo couenne",
    module="idaes_fi.structfs.actions.tests.test_solver",
)


@FS.step(Steps.build)
def build(ctx):
    ctx.model = build_flowsheet()


@FS.step(Steps.set_operating_conditions)
def set_operating_conditions(ctx):
    set_dof(ctx.model)


@FS.step(Steps.set_scaling)
def runner_set_scaling(ctx):
    set_scaling(ctx.model)


@FS.step(Steps.solve_initial)
def solve_initial(ctx):
    initialize_flowsheet(ctx.model)


@FS.step(Steps.set_solver)
def set_solver(ctx):
    ctx.solver = _solver_name


@FS.step(Steps.solve_optimization)
def runner_solve_flowsheet(ctx):
    ctx.results = solve_flowsheet(ctx.model, ctx.solver, stee=True)


#########
# Tests #
#########


@pytest.mark.integration
@pytest.mark.parametrize(
    "solver_name", ["ipopt", "couenne", "doesnotexistandneverwill"]
)
def test_solver_action(solver_name):
    """Test the solver action."""
    global _solver_name
    _solver_name = solver_name

    FS.run_steps()
    actions = FS.report()["actions"]
    for step in actions["progress"]["steps"]:
        name = step["name"]
        print(f"examine {solver_name} step {name}: {step['status']}")
        if step["status"] == "failed":
            # couenne doesn't solve the optimization
            if _solver_name == "couenne" and name == Steps.solve_optimization:
                solver_output = actions[ActionNames.SOLVER_OUTPUT.value]["output"]
                print(f"Solver output:\n{solver_output}")
                print(f"Step error: {step['err']}")
                assert "Couenne" in solver_output[name]
            # only build step is OK for the bad solver
            elif _solver_name == "doesnotexistandneverwill" and name != Steps.build:
                pass
            # ipopt should solve everything
            elif _solver_name == "ipopt":
                print(f"Step failed: {name}: {step['err']}")
                assert False
            # guard against unexpected values
            else:
                assert False
