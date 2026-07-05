"""
Steady state directional solidification model
"""

import numpy as np

from solidification_tool.core.settings import EngineSettings


def solve_steady_state_directional(inputs, settings: EngineSettings | None = None):
    """
    Solves thermal gradient versus solidification velocity for steady-state directional solidification
    """

    k = inputs.k_l
    rho = inputs.rho_s
    cp = inputs.c_p
    Lf = inputs.L_f
    Tf = inputs.T_f
    T0 = inputs.T_o

    settings = settings or EngineSettings()
    V = np.logspace(settings.heat_v_min_exp, settings.heat_v_max_exp, settings.heat_v_count)

    G = V * ( ( ( (rho * cp) / (k) ) * (Tf-T0) ) - ( (Lf * rho) / (k) ) )

    return ( V, G )




