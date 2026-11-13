"""
Test for the solver action.
"""

from idaes_fi import FlowsheetRunner, Steps
from idaes_fi.tests.demo_flowsheet import *

import pytest

_solver_name = "couenne"

##############################
# Create a wrapped flowsheet #
##############################

f1_runner = FlowsheetRunner(
    steps=[
        Steps.build,
        Steps.set_operating_conditions,
        Steps.set_scaling,
        Steps.solve_initial,
        Steps.set_solver,
        Steps.solve_optimization,
    ],
)


def main(runner: FlowsheetRunner):
    runner.step_begin(Steps.build)
    runner.model = model = build_flowsheet()

    runner.step_begin(Steps.set_operating_conditions)
    set_dof(model)

    runner.step_begin(Steps.set_scaling)
    set_scaling(model)

    runner.step_begin(Steps.solve_initial)
    initialize_flowsheet(model)

    runner.step_begin(Steps.set_solver)
    try:
        solver = get_solver(_solver_name)
    except KeyError:
        print(f"Could not get solver '{_solver_name}'")
        raise

    runner.step_begin(Steps.solve_optimization)
    results = solve_flowsheet(model, solver, stee=True)
    runner.solve_result = results

    return model


f1_runner.main = main  # don't forget this

#########
# Tests #
#########


@pytest.mark.integration
@pytest.mark.parametrize(
    "solver_name", ["ipopt", "couenne", "doesnotexistandneverwill"]
)
def test_solver_action(solver_name, tmp_path):
    """Test the solver action."""
    global _solver_name
    _solver_name = solver_name

    f1_runner.report_db_file = tmp_path / "report.db"
    f1_runner.run_flowsheet()
    actions = f1_runner.report["actions"]
    progress_action_name = "Progress"
    solver_action_name = "CaptureSolverOutput"
    for step in actions[progress_action_name]["steps"]:
        name = step["name"]
        print(f"examine {solver_name} step {name}: {step['status']}")
        if step["status"] == "failed":
            failed = True
            # couenne doesn't solve the optimization
            if _solver_name == "couenne":
                assert name in (Steps.set_solver, Steps.solve_optimization)
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
