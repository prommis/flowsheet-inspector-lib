from pyomo.environ import ConcreteModel, SolverFactory
from idaes.core import FlowsheetBlock

# Import idaes logger to set output levels
import idaes.logger as idaeslog
from idaes.models.properties.activity_coeff_models.BTX_activity_coeff_VLE import (
    BTXParameterBlock,
)
from idaes.models.unit_models import Flash

from idaes_fi.structfs import fi_main


def build():
    m = ConcreteModel()
    m.fs = FlowsheetBlock(dynamic=False)
    m.fs.properties = BTXParameterBlock(
        valid_phase=("Liq", "Vap"), activity_coeff_model="Ideal", state_vars="FTPz"
    )
    m.fs.flash = Flash(property_package=m.fs.properties)
    # assert degrees_of_freedom(m) == 7
    m.fs.flash.inlet.flow_mol.fix(1)
    m.fs.flash.inlet.temperature.fix(368)
    m.fs.flash.inlet.pressure.fix(101325)
    m.fs.flash.inlet.mole_frac_comp[0, "benzene"].fix(0.5)
    m.fs.flash.inlet.mole_frac_comp[0, "toluene"].fix(0.5)
    m.fs.flash.heat_duty.fix(0)
    m.fs.flash.deltaP.fix(0)

    return m


def initialize(m):
    m.fs.flash.initialize(outlvl=idaeslog.INFO)


### end basic Flash flowsheet code


@fi_main()
def my_main():
    """Create and solve Flash flowsheet"""

    m = build()
    initialize(m)

    solver = SolverFactory("ipopt")
    result = solver.solve(m, tee=True)

    return m, result
