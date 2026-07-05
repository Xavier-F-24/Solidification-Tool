import numpy as np
from solidification_tool.core.settings import EngineSettings


def solve_pdas(inputs, V_min, V_max, fit_ims_results, settings: EngineSettings | None = None):
    """
    Compute G(V) curves for prescribed primary dendrite arm spacings (lambda1)
    """

    # --------------------------------------------------
    # Prescribed PDAS values (meters)
    # --------------------------------------------------
    settings = settings or EngineSettings()
    lambda_list = np.logspace(settings.spacing_min_exp, settings.spacing_max_exp, settings.spacing_count)

    # --------------------------------------------------
    # Fit IMS power laws at desired G
    # --------------------------------------------------
    alpha1 = fit_ims_results["alpha1"]
    beta1 = fit_ims_results["beta1"]
    alpha2 = fit_ims_results["alpha2"]
    beta2 = fit_ims_results["beta2"]

    # --------------------------------------------------
    # Velocity grid (physically bounded)
    # --------------------------------------------------
    V_grid = np.logspace(np.log10(V_min), np.log10(V_max), settings.spacing_v_count)

    DeltaT0 = inputs.NonEq_Freezing_range

    # --------------------------------------------------
    # IMS-derived terms
    # --------------------------------------------------
    R = alpha1 * V_grid**beta1
    DeltaT = alpha2 * V_grid**beta2
    DeltaT_eff = DeltaT0 - DeltaT

    # Physical validity
    valid = DeltaT_eff > 0

    # --------------------------------------------------
    # Store results
    # --------------------------------------------------
    pdas_curves = {}

    for lambda1 in lambda_list:
        G = np.full_like(V_grid, np.nan)
        G[valid] = (3.0 * R[valid] * DeltaT_eff[valid]) / (lambda1**2)

        pdas_curves[lambda1] = {
            "V": V_grid[valid],
            "G": G[valid]
        }

    return pdas_curves

