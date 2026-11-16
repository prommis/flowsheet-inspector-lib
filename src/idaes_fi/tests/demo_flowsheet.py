#################################################################################
# Process Optimization and Modeling for Minerals Sustainability (PrOMMiS) Copyright (c) 2023-2026
#
# “Process Optimization and Modeling for Minerals Sustainability (PrOMMiS)” was produced under the DOE
# Process Optimization and Modeling for Minerals Sustainability (“PrOMMiS”) initiative, and is
# copyrighted by the software owners: The Regents of the University of California, through Lawrence
# Berkeley National Laboratory, National Technology & Engineering Solutions of Sandia, LLC through
# Sandia National Laboratories, Carnegie Mellon University, University of Notre Dame, and West
# Virginia University Research Corporation.
#
# NOTICE. This Software was developed under funding from the U.S. Department of Energy and the
# U.S. Government consequently retains certain rights. As such, the U.S. Government has been granted
# for itself and others acting on its behalf a paid-up, nonexclusive, irrevocable, worldwide license
# in the Software to reproduce, distribute copies to the public, prepare derivative works, and perform
# publicly and display publicly, and to permit other to do so.
#
#################################################################################
"""
Demonstration flowsheet for testing purposes.

Constructs a basic flowsheet for a benzene-toluene system with a mixer, heater
and flash unit.
"""

# stdlib
import time

# third-party imports
import idaes.logger as idaeslog
from idaes.core.solvers import get_solver

# local imports
from idaes_fi import FlowsheetRunner, Steps

_steps = (
    Steps.build,
    Steps.set_scaling,
    Steps.initialize,
    Steps.set_solver,
    Steps.solve_optimization,
)
f1_runner = FlowsheetRunner(steps=_steps)

# for testing purposes, create another runner we never use
f2_runner = FlowsheetRunner(steps=_steps)


def build_flowsheet():
    """Build demo flowsheet"""
    from pyomo.environ import ConcreteModel, TransformationFactory
    from pyomo.network import Arc
    from idaes.core import FlowsheetBlock
    from idaes.models.properties.activity_coeff_models.BTX_activity_coeff_VLE import (
        BTXParameterBlock,
    )
    from idaes.models.unit_models import Mixer, Heater, Flash

    # defer here because these take >2 seconds to import

    m = ConcreteModel()

    m.fs = FlowsheetBlock(dynamic=False)

    m.fs.BT_props = BTXParameterBlock()

    m.fs.M01 = Mixer(property_package=m.fs.BT_props)

    m.fs.H02 = Heater(property_package=m.fs.BT_props)

    m.fs.F03 = Flash(property_package=m.fs.BT_props)

    m.fs.s01 = Arc(source=m.fs.M01.outlet, destination=m.fs.H02.inlet)
    m.fs.s02 = Arc(source=m.fs.H02.outlet, destination=m.fs.F03.inlet)

    TransformationFactory("network.expand_arcs").apply_to(m.fs)

    return m


def set_scaling(m):
    """Set scaling for demo flowsheet"""
    import idaes.core.util.scaling as iscale

    iscale.set_scaling_factor(m.fs.M01.inlet_1_state[0].flow_mol_phase, 1e6)
    iscale.set_scaling_factor(m.fs.M01.inlet_1_state[0].flow_mol_phase["Liq"], 1e6)
    iscale.set_scaling_factor(m.fs.M01.inlet_1_state[0].flow_mol_phase["Vap"], 1)
    iscale.set_scaling_factor(
        m.fs.M01.inlet_1_state[0].mole_frac_phase_comp["Liq", "benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_1_state[0].mole_frac_phase_comp["Vap", "benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_1_state[0].mole_frac_phase_comp["Liq", "toluene"], 1e5
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_1_state[0].mole_frac_phase_comp["Vap", "toluene"], 1e6
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_1_state[0].pressure_sat_comp["benzene"], 1e-5
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_1_state[0].pressure_sat_comp["toluene"], 1e-4
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_1_state[0].enth_mol_phase_comp["Liq", "benzene"], 1e-4
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_1_state[0].enth_mol_phase_comp["Vap", "benzene"], 1e-4
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_1_state[0].enth_mol_phase_comp["Liq", "toluene"], 1e-4
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_1_state[0].enth_mol_phase_comp["Vap", "toluene"], 1e-4
    )

    iscale.set_scaling_factor(m.fs.M01.inlet_2_state[0].flow_mol_phase, 1e1)
    iscale.set_scaling_factor(m.fs.M01.inlet_2_state[0].flow_mol_phase["Vap"], 1e1)

    iscale.set_scaling_factor(
        m.fs.M01.inlet_2_state[0].mole_frac_phase_comp["Liq", "benzene"], 1e5
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_2_state[0].mole_frac_phase_comp["Vap", "benzene"], 1e5
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_2_state[0].mole_frac_phase_comp["Liq", "toluene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_2_state[0].mole_frac_phase_comp["Vap", "toluene"], 1
    )

    iscale.set_scaling_factor(
        m.fs.M01.inlet_2_state[0].pressure_sat_comp["benzene"], 1e-6
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_2_state[0].pressure_sat_comp["toluene"], 1e-6
    )

    iscale.set_scaling_factor(
        m.fs.M01.inlet_2_state[0].enth_mol_phase_comp["Liq", "benzene"], 1e-4
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_2_state[0].enth_mol_phase_comp["Vap", "benzene"], 1e-4
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_2_state[0].enth_mol_phase_comp["Liq", "toluene"], 1e-4
    )
    iscale.set_scaling_factor(
        m.fs.M01.inlet_2_state[0].enth_mol_phase_comp["Vap", "toluene"], 1e-4
    )

    iscale.set_scaling_factor(
        m.fs.M01.mixed_state[0].enth_mol_phase_comp["Liq", "benzene"], 1e-4
    )
    iscale.set_scaling_factor(
        m.fs.M01.mixed_state[0].enth_mol_phase_comp["Vap", "benzene"], 1e-4
    )
    iscale.set_scaling_factor(
        m.fs.M01.mixed_state[0].enth_mol_phase_comp["Liq", "toluene"], 1e-4
    )
    iscale.set_scaling_factor(
        m.fs.M01.mixed_state[0].enth_mol_phase_comp["Vap", "toluene"], 1e-4
    )
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].enthalpy_flow_terms["Liq"], 1)
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].enthalpy_flow_terms["Vap"], 1)
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].eq_total, 1)
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].eq_sum_mol_frac, 1)
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].eq_mol_frac_out, 1)
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].eq_comp["benzene"], 1)
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].eq_comp["toluene"], 1)
    iscale.set_scaling_factor(
        m.fs.M01.mixed_state[0].eq_phase_equilibrium["benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.M01.mixed_state[0].eq_phase_equilibrium["toluene"], 1
    )
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].eq_P_vap["benzene"], 1)
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].eq_P_vap["toluene"], 1)

    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].pressure, 1e-5)
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].pressure_sat_comp, 1e-5)
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].temperature, 1e-2)
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].flow_mol, 1)
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].flow_mol_phase, 1)
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].mole_frac_comp["benzene"], 1e1)
    iscale.set_scaling_factor(m.fs.M01.mixed_state[0].mole_frac_comp["toluene"], 1e1)

    iscale.set_scaling_factor(m.fs.H02.control_volume.heat, 1e-5)
    iscale.set_scaling_factor(m.fs.H02.control_volume.properties_in[0].pressure, 1e-5)
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0].pressure_sat_comp, 1e-5
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0].temperature, 1e-2
    )
    iscale.set_scaling_factor(m.fs.H02.control_volume.properties_in[0].flow_mol, 1)
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0].flow_mol_phase, 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0].mole_frac_comp["benzene"], 1e1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0].mole_frac_comp["toluene"], 1e1
    )
    iscale.set_scaling_factor(m.fs.H02.control_volume.properties_out[0].flow_mol, 1)
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0].flow_mol_phase, 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0].mole_frac_comp["benzene"], 1e1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0].mole_frac_comp["toluene"], 1e1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0].temperature, 1e-2
    )
    iscale.set_scaling_factor(m.fs.H02.control_volume.properties_out[0].pressure, 1e-5)
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0].pressure_sat_comp, 1e-5
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0].enth_mol_phase_comp["Liq", "benzene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0].enth_mol_phase_comp["Vap", "benzene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0].enth_mol_phase_comp["Liq", "toluene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0].enth_mol_phase_comp["Vap", "toluene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0].eq_comp["benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0].eq_comp["toluene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0].eq_comp["benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0].eq_comp["toluene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0].eq_phase_equilibrium["benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0].eq_phase_equilibrium["toluene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0].eq_phase_equilibrium["benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0].eq_phase_equilibrium["toluene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0.0].eq_P_vap["benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0.0].eq_P_vap["toluene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0.0].eq_P_vap["benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0.0].eq_P_vap["toluene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0].enth_mol_phase_comp["Liq", "benzene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0].enth_mol_phase_comp["Vap", "benzene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0].enth_mol_phase_comp["Liq", "toluene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0].enth_mol_phase_comp["Vap", "toluene"],
        1e-4,
    )
    iscale.set_scaling_factor(m.fs.H02.control_volume.properties_in[0.0].eq_total, 1)
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0.0].eq_sum_mol_frac, 1
    )
    iscale.set_scaling_factor(m.fs.H02.control_volume.properties_out[0.0].eq_total, 1)
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0.0].eq_sum_mol_frac, 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_out[0.0].eq_mol_frac_out, 1
    )

    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0.0].material_flow_terms[
            "Liq", "benzene"
        ],
        1,
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0.0].material_flow_terms[
            "Vap", "benzene"
        ],
        1,
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0.0].material_flow_terms[
            "Liq", "toluene"
        ],
        1,
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0.0].material_flow_terms[
            "Vap", "toluene"
        ],
        1,
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0.0].enthalpy_flow_terms["Liq"], 1
    )
    iscale.set_scaling_factor(
        m.fs.H02.control_volume.properties_in[0.0].enthalpy_flow_terms["Vap"], 1
    )

    iscale.set_scaling_factor(m.fs.F03.control_volume.heat, 1)
    iscale.set_scaling_factor(m.fs.F03.control_volume.properties_in[0].pressure, 1e-5)
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0].pressure_sat_comp, 1e-5
    )
    iscale.set_scaling_factor(m.fs.F03.control_volume.properties_out[0].pressure, 1e-5)
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0].pressure_sat_comp, 1e-5
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0].temperature, 1e-2
    )
    iscale.set_scaling_factor(m.fs.F03.control_volume.properties_in[0].flow_mol, 1)
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0].flow_mol_phase, 1
    )
    iscale.set_scaling_factor(m.fs.F03.control_volume.properties_out[0].flow_mol, 1)
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0].flow_mol_phase, 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0].mole_frac_comp["benzene"], 1e1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0].mole_frac_comp["toluene"], 1e1
    )

    iscale.set_scaling_factor(m.fs.F03.control_volume.properties_in[0.0].eq_total, 1)
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0.0].eq_sum_mol_frac, 1
    )
    iscale.set_scaling_factor(m.fs.F03.control_volume.properties_out[0.0].eq_total, 1)
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0.0].eq_sum_mol_frac, 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0.0].eq_mol_frac_out, 1
    )

    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0].enth_mol_phase_comp["Liq", "benzene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0].enth_mol_phase_comp["Vap", "benzene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0].enth_mol_phase_comp["Liq", "toluene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0].enth_mol_phase_comp["Vap", "toluene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0].enth_mol_phase_comp["Liq", "benzene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0].enth_mol_phase_comp["Vap", "benzene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0].enth_mol_phase_comp["Liq", "toluene"],
        1e-4,
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0].enth_mol_phase_comp["Vap", "toluene"],
        1e-4,
    )

    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0].eq_comp["benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0].eq_comp["toluene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0].eq_comp["benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0].eq_comp["toluene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0].eq_phase_equilibrium["benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0].eq_phase_equilibrium["toluene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0].eq_phase_equilibrium["benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0].eq_phase_equilibrium["toluene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0.0].eq_P_vap["benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0.0].eq_P_vap["toluene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0.0].eq_P_vap["benzene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_out[0.0].eq_P_vap["toluene"], 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0.0].material_flow_terms[
            "Liq", "benzene"
        ],
        1,
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0.0].material_flow_terms[
            "Vap", "benzene"
        ],
        1,
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0.0].material_flow_terms[
            "Liq", "toluene"
        ],
        1,
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0.0].material_flow_terms[
            "Vap", "toluene"
        ],
        1,
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0.0].enthalpy_flow_terms["Liq"], 1
    )
    iscale.set_scaling_factor(
        m.fs.F03.control_volume.properties_in[0.0].enthalpy_flow_terms["Vap"], 1
    )

    iscale.calculate_scaling_factors(m)


def set_dof(m):
    """Set degrees of freedom for demo flowsheet"""
    eps = 1e-5
    m.fs.M01.inlet_1.flow_mol.fix(1.0)
    m.fs.M01.inlet_1.mole_frac_comp[:, "benzene"].fix(1 - eps)
    m.fs.M01.inlet_1.mole_frac_comp[:, "toluene"].fix(eps)
    m.fs.M01.inlet_1.pressure.fix(101325)
    m.fs.M01.inlet_1.temperature.fix(370)

    m.fs.M01.inlet_2.flow_mol.fix(1.0)
    m.fs.M01.inlet_2.mole_frac_comp[:, "benzene"].fix(eps)
    m.fs.M01.inlet_2.mole_frac_comp[:, "toluene"].fix(1 - eps)
    m.fs.M01.inlet_2.pressure.fix(1.3e5)
    m.fs.M01.inlet_2.temperature.fix(380)

    m.fs.H02.outlet.temperature[0].fix(370)

    m.fs.F03.heat_duty.fix(1e-6)
    m.fs.F03.deltaP.fix(1e-6)


def initialize_flowsheet(m):
    """Initialize demo flowsheet"""
    from idaes.core.util.initialization import propagate_state

    m.fs.M01.initialize(outlvl=idaeslog.WARNING)

    propagate_state(m.fs.s01)
    m.fs.H02.initialize(outlvl=idaeslog.WARNING)
    propagate_state(m.fs.s02)
    m.fs.F03.initialize(outlvl=idaeslog.WARNING)


def solve_flowsheet(m, solver, stee=False):
    """Solve demo flowsheet"""
    return solver.solve(m, tee=stee)


def display_results(m):
    """Display results for flowsheet"""
    print(banner("results", 65))
    m.fs.M01.outlet.display()
    m.fs.H02.outlet.display()
    m.fs.F03.vap_outlet.display()
    m.fs.F03.liq_outlet.display()


def main(runner):
    runner.step_begin(Steps.build)
    runner.model = m = build_flowsheet()

    runner.step_begin(Steps.set_scaling)
    set_scaling(m)
    runner.step_end()

    set_dof(m)

    runner.step_begin(Steps.initialize)
    initialize_flowsheet(m)

    runner.step_begin(Steps.set_solver)
    solver = get_solver()

    runner.step_begin(Steps.solve_optimization)
    runner.solve_result = solve_flowsheet(m, solver, stee=True)
    ## For testing: make it fail!
    # m.fs.F03.heat_duty.fix(1e6)
    # runner.solve_result = solve_flowsheet(m, solver, stee=True)

    print(f"Demo flowsheet solved, returning model: {m}")
    return m


def twiddle_thumbs(sec: int):
    try:
        for i in range(sec):
            time.sleep(1)
            print(f"{sec - i} ", end="", flush=True)
        print()
    except KeyboardInterrupt:
        print(" -- twiddlus interruptus!")
        raise


def slow_main(runner):
    runner.step_begin(Steps.build)
    runner.model = m = build_flowsheet()

    runner.step_begin(Steps.set_scaling)
    set_scaling(m)
    runner.step_end()

    set_dof(m)

    runner.step_begin(Steps.initialize)
    initialize_flowsheet(m)
    twiddle_thumbs(60)

    runner.step_begin(Steps.set_solver)
    solver = get_solver()

    runner.step_begin(Steps.solve_optimization)
    twiddle_thumbs(60)
    runner.solve_result = solve_flowsheet(m, solver, stee=True)
    twiddle_thumbs(60)

    ## For testing: make it fail!
    # m.fs.F03.heat_duty.fix(1e6)
    # runner.solve_result = solve_flowsheet(m, solver, stee=True)

    print(f"Demo flowsheet solved, returning model: {m}")
    return m


f1_runner.main = main
f2_runner.main = slow_main


def banner(title: str, width: int):
    title = title.upper()
    n = len(title)
    if (width - n) % 2 == 1:
        width += 1
    spc = " " * ((width - n) // 2)
    return "\n".join(
        [
            "+" + "-" * width + "+",
            "|" + spc + title + spc + "|",
            "+" + "-" * width + "+",
        ]
    )


if __name__ == "__main__":
    m = f1_runner.run_flowsheet()
    display_results(m)
