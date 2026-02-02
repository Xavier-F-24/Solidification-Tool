"""
Steady state directional solidification model
"""

import numpy as np

def solve_steady_state_directional(inputs):
    """
    Solves thermal gradient versus solidification velocity for steady-state directional solidification
    """

    k = inputs.k_l
    rho = inputs.rho_s
    cp = inputs.c_p
    Lf = inputs.L_f
    Tf = inputs.T_f
    T0 = inputs.T_o

    V = np.logspace(-6,6,100)

    G = V * ( ( ( (rho * cp) / (k) ) * (Tf-T0) ) - ( (Lf * rho) / (k) ) )

    return ( V, G )




