"""
Ivantsov Multiple Solutes undercooling model
"""

import numpy as np

from IMS_model.ivantsov import Ivantsov

import numpy as np
from IMS_model.ivantsov import Ivantsov


def solve_ims(inputs):
    """
    Multi-solute Ivantsov + marginal stability solver (vectorized in G).

    Axis convention (STRICT):
        Axis 0 -> Thermal gradient G
        Axis 1 -> Solute index
        Axis 2 -> Peclet number

    All internal arrays respect (n_G, n_solute, n_Pe)

    Written Jan 2026, XF
    """

    # --------------------------------------------------
    # Unpack inputs
    # --------------------------------------------------
    C_0 = np.atleast_1d(inputs.C_0)[:, None]    # (n_solute, 1)
    k   = np.atleast_1d(inputs.k)[:, None]
    m   = np.atleast_1d(inputs.m)[:, None]
    D   = np.atleast_1d(inputs.D)[:, None]

    Gamma = float(inputs.Gamma)

    N_g = 100
    G = np.logspace(-6, 12, N_g)                     # (n_G,)
    G = G[:, None, None]                         # (n_G, 1, 1)

    n_solute = C_0.shape[0]

    # --------------------------------------------------
    # Peclet construction (solute-scaled)
    # --------------------------------------------------
    N_Pe = 200
    P = np.logspace(-9, 9, N_Pe)                 # (n_Pe,)

    D_ref = D[0, 0]
    scale = D_ref / D                            # (n_solute, 1)

    Pe = scale * P[None, :]                      # (n_solute, n_Pe)
    Pe = Pe[None, :, :]                          # (1, n_solute, n_Pe)

    # --------------------------------------------------
    # Ivantsov + solutal response
    # --------------------------------------------------
    Iv = Ivantsov(Pe)                            # (1, n_solute, n_Pe)

    k3  = k[None, :, :]
    m3  = m[None, :, :]
    C03 = C_0[None, :, :]

    Eta = 1 - (2 * k3) / (
        2 * k3 - 1 + np.sqrt(1 + (2 * np.pi / Pe)**2)
    )

    C_l_star = C03 / (1 - (1 - k3) * Iv)

    # Solutal term inside stability equation
    S = m3 * Pe * (1 - k3) * C_l_star * Eta       # (1, n_solute, n_Pe)

    # --------------------------------------------------
    # Marginal stability quadratic
    # A/R² + B/R + G = 0
    # --------------------------------------------------
    A = 4 * np.pi**2 * Gamma                     # scalar

    B = 2 * np.sum(S, axis=1)                    # (1, n_Pe)
    B = B[None, :, :]                            # (1, 1, n_Pe)

    disc = B**2 - 4 * A * G                      # (n_G, 1, n_Pe)
    valid = disc > 0

    Quad_plus  = np.full_like(disc, np.nan)
    Quad_minus = np.full_like(disc, np.nan)

    sqrt_disc = np.zeros_like(disc)
    sqrt_disc[valid] = np.sqrt(disc[valid])

    Quad_plus[valid]  = (-B + sqrt_disc)[valid] / (2 * A)
    Quad_minus[valid] = (-B - sqrt_disc)[valid] / (2 * A)

    # --------------------------------------------------
    # Tip radius
    # --------------------------------------------------
    R_plus  = 1 / Quad_plus                      # (n_G, 1, n_Pe)
    R_minus = 1 / Quad_minus

    R_plus  = R_plus[:, 0, :]                    # (n_G, n_Pe)
    R_minus = R_minus[:, 0, :]

    # --------------------------------------------------
    # Tip velocity (reference diffusivity)
    # --------------------------------------------------
    V_plus  = 2 * D_ref * Pe / R_plus[:, None, :]
    V_minus = 2 * D_ref * Pe / R_minus[:, None, :]

    # --------------------------------------------------
    # Undercooling components
    # --------------------------------------------------
    Solute_undercooling = m3 * (C03 - C_l_star)      # (1, n_solute, n_Pe)

    DeltaT_solute = np.sum(Solute_undercooling, axis=1)  # (1, n_Pe)
    DeltaT_solute = DeltaT_solute[None, :, :]        # (1, 1, n_Pe)

    R_tip = np.minimum(R_plus, R_minus)
    Curvature_undercooling = 2 * Gamma / R_tip       # (n_G, n_Pe)

    Total_undercooling = DeltaT_solute + Curvature_undercooling[:, None, :]
    Total_undercooling = Total_undercooling[:, 0, :] # (n_G, n_Pe)

    # --------------------------------------------------
    # Output
    # --------------------------------------------------
    return {
        
        "G": G[:, 0, 0],                              # (n_G,)
        "Pe": Pe[0],                                  # (n_solute, n_Pe)
        "R+": R_plus,                                 # (n_G, n_Pe)
        "R-": R_minus,
        "V+": V_plus,                                 # (n_G, n_Pe)
        "V-": V_minus,                                # (n_G, n_Pe)
        "Total_undercooling": Total_undercooling,     # (n_G, n_Pe)
        "Stable": valid[:, 0, :],                     # (n_G, n_Pe)
        "Solute_undercooling": Solute_undercooling[0],
        "Curvature_undercooling": Curvature_undercooling
    }
