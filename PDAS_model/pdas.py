import numpy as np

def solve_pdas(inputs, V_min, V_max, fit_ims_results):
    """
    Compute G(V) curves for prescribed primary dendrite arm spacings (lambda1)
    """

    # --------------------------------------------------
    # Prescribed PDAS values (meters)
    # --------------------------------------------------
    lambda_list = np.logspace(-6, 6, 12)  # 1 µm → 1 mm (adjust freely)

    # --------------------------------------------------
    # Fit IMS power laws at desired G
    # --------------------------------------------------
    alpha1, beta1, alpha2, beta2 = fit_ims_results

    # --------------------------------------------------
    # Velocity grid (physically bounded)
    # --------------------------------------------------
    V_grid = np.logspace(np.log10(V_min), np.log10(V_max), 100)

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

