import numpy as np

def solve_sdas(inputs, V_min, V_max):
    """
    Compute G(V) curves for prescribed secondary dendrite arm spacings (lambda2)
    """

    # --------------------------------------------------
    # Prescribed PDAS values (meters)
    # --------------------------------------------------
    lambda_list = np.logspace(-6, 6, 12)  # 1 µm → 1 mm (adjust freely)

    # --------------------------------------------------
    # Velocity grid (physically bounded)
    # --------------------------------------------------
    V_grid = np.logspace(np.log10(V_min), np.log10(V_max), 100)

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
    
    M_1 = -Gamma / (np.sum( (m * (np.full_like(k, 1) - k) * (C_f - C_0)) / D ))
    M_2 = np.sum( (m * (np.full_like(k, 1) - k) * C_f) / D)
    M_3 = np.sum( (m * (np.full_like(k, 1) - k) * C_0) / D)

    M = M_1 * np.log( M_2 / M_3 )

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

