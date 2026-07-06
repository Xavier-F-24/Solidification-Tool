import numpy as np
from scipy.optimize import brentq
from solidification_tool.core.settings import EngineSettings
from solidification_tool.core.validation import EngineComputationError

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
    V_max = 1e6,
    max_expansions = 20 ):
    """
    Solve for V such that CET G(V) = G_out.
    """
    if not all(np.isfinite(value) and value > 0 for value in [G_out, alpha, beta, n, DeltaT_nuc, N0, phi, V_min, V_max]):
        raise EngineComputationError("CET root solve requires positive finite inputs.")
    if phi >= 1:
        raise EngineComputationError("CET root solve requires phi to be between 0 and 1.")
    if V_min >= V_max:
        raise EngineComputationError("CET root solve requires V_min < V_max.")

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

    lower = f(V_min)
    upper = f(V_max)
    expansions = 0
    while upper < 0 and expansions < max_expansions:
        V_max *= 10.0
        upper = f(V_max)
        expansions += 1

    if not np.isfinite(lower) or not np.isfinite(upper) or lower * upper > 0:
        raise EngineComputationError("CET could not bracket a transition velocity for the requested G.")

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
    if not np.isfinite(V_min) or not np.isfinite(V_max) or V_min <= 0 or V_max <= 0 or V_min >= V_max:
        raise EngineComputationError("CET requires positive finite V_min < V_max.")
    if len(G_out) == 0 or not np.all(np.isfinite(G_out)) or np.min(G_out) <= 0:
        raise EngineComputationError("CET requires positive finite stability G values.")
    if not np.isfinite(alpha2) or alpha2 <= 0 or not np.isfinite(beta2) or beta2 <= 0:
        raise EngineComputationError("CET requires positive finite IMS undercooling fit coefficients.")
    
    # CET exponent inferred from the IMS undercooling power-law fit.
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
