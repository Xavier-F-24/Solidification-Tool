import numpy as np
from scipy.optimize import brentq
from solidification_tool.core.settings import EngineSettings

def solve_V_for_G(
    G_out,
    *,
    alpha,
    beta,
    n,
    DeltaT_nuc,
    N0,
    phi,
    V_min = 1e-12,
    V_max = 1e6 ):
    """
    Solve for V such that CET G(V) = G_out.
    """

    # CET prefactor
    A = (1.0 / (n + 1.0)) * (
        (-4.0 * np.pi * N0) / (3.0 * np.log(1.0 - phi))
    ) ** (1.0 / 3.0)

    C1 = A * alpha
    C2 = A * DeltaT_nuc ** (n + 1) / alpha ** n

    def f(V):
        return (
            C1 * V ** beta
            - C2 * V ** (-beta * n)
            - G_out
        )

    # Expand upper bound automatically if needed
    while f(V_max) < 0:
        V_max *= 10.0

    V_root = brentq(f, V_min, V_max)
    return V_root


def solve_cet(inputs, V_min, V_max, fit_ims_results, G_out, settings: EngineSettings | None = None):
    """
    Compute G(V) curves for Columnar to Equiaxed transitions of 0.01 and 0.5 (standard)
    """
    settings = settings or EngineSettings()
    phi_list = list(settings.cet_phi_values)

    DeltaT0 = inputs.NonEq_Freezing_range
    N0 = inputs.N0
    DeltaTN = inputs.DeltaTN

    alpha1 = fit_ims_results["alpha1"]
    beta1 = fit_ims_results["beta1"]
    alpha2 = fit_ims_results["alpha2"]
    beta2 = fit_ims_results["beta2"]
    
    # --------------------------------------------------
    # Lets solve
    # --------------------------------------------------
    n = 1 / beta2

    # --------------------------------------------------
    # Store results
    # --------------------------------------------------
    cet_results = {}

    for phi in phi_list:
        V_end = solve_V_for_G(
        G_out = np.min(G_out),
        alpha = alpha2,
        beta = beta2,
        n = n,
        DeltaT_nuc = DeltaTN,
        N0 = N0,
        phi = phi
        )

        V_grid = np.logspace(np.log10(V_end), np.log10(V_max), settings.cet_v_count)

        DeltaT = alpha2 * V_grid ** beta2

        G = np.full_like(V_grid, np.nan)
        G = (1 / (n + 1)) * (( (-4*np.pi*N0) / (3 * np.log(1 - phi)) )**(1 / 3) ) * DeltaT * (1 - (DeltaTN ** (n + 1)) / (DeltaT ** (n + 1)) )

        cet_results[phi] = {
            "V": V_grid,
            "G": G
        }

    return(cet_results, phi_list)
