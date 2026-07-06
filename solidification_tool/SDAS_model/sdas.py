import numpy as np
from solidification_tool.core.settings import EngineSettings
from solidification_tool.core.validation import EngineComputationError


def solve_sdas(inputs, V_min, V_max, settings: EngineSettings | None = None):
    """
    Compute G(V) curves for prescribed secondary dendrite arm spacings (lambda2)
    """

    # --------------------------------------------------
    # Prescribed PDAS values (meters)
    # --------------------------------------------------
    settings = settings or EngineSettings()
    lambda_list = np.logspace(settings.spacing_min_exp, settings.spacing_max_exp, settings.spacing_count)
    if not np.isfinite(V_min) or not np.isfinite(V_max) or V_min <= 0 or V_max <= 0 or V_min >= V_max:
        raise EngineComputationError("SDAS requires positive finite V_min < V_max.")

    # --------------------------------------------------
    # Velocity grid (physically bounded)
    # --------------------------------------------------
    V_grid = np.logspace(np.log10(V_min), np.log10(V_max), settings.spacing_v_count)

    C_0 = np.atleast_1d(inputs.C_0)[:, None]    # (n_solute, 1)
    C_f = np.atleast_1d(inputs.C_f)[:, None]
    k   = np.atleast_1d(inputs.k)[:, None]
    m   = np.atleast_1d(inputs.m)[:, None]
    D   = np.atleast_1d(inputs.D)[:, None]

    DeltaT0 = inputs.NonEq_Freezing_range
    Gamma = inputs.Gamma

    # --------------------------------------------------
    # lambda2 = 5.5 * (M * t_f)**(1/3); M = big sums
    # --------------------------------------------------
    
    denominator = np.sum((m * (np.full_like(k, 1) - k) * (C_f - C_0)) / D)
    if not np.isfinite(denominator) or denominator == 0:
        raise EngineComputationError("SDAS denominator for coarsening coefficient is zero or non-finite.")

    M_1 = -Gamma / denominator
    M_2 = np.sum( (m * (np.full_like(k, 1) - k) * C_f) / D)
    M_3 = np.sum( (m * (np.full_like(k, 1) - k) * C_0) / D)
    ratio = M_2 / M_3
    if not np.isfinite(ratio) or ratio <= 0:
        raise EngineComputationError("SDAS logarithm argument M_2/M_3 must be positive and finite.")

    M = M_1 * np.log(ratio)
    if not np.isfinite(M) or M <= 0:
        raise EngineComputationError("SDAS coarsening coefficient M must be positive and finite.")

    # --------------------------------------------------
    # Store results
    # --------------------------------------------------
    sdas_curves = {}

    for lambda2 in lambda_list:
        G = np.full_like(V_grid, np.nan)
        G = (M * DeltaT0) / ( V_grid *((lambda2**3) / (5.5**3)))

        sdas_curves[lambda2] = {
            "V": V_grid,
            "G": G
        }

    return sdas_curves

