import numpy as np

def solve_cet(inputs, V_min, V_max, fit_ims_results):
    """
    Compute G(V) curves for Columnar to Equiaxed transitions of 0.01 and 0.5 (standard)
    """
    # --------------------------------------------------
    # Velocity grid (physically bounded)
    # --------------------------------------------------
    V_grid = np.logspace(np.log10(V_min), np.log10(V_max), 100)

    phi_list = [0.01, 0.5]

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

    DeltaT = alpha2 * V_grid ** beta2

    # --------------------------------------------------
    # Store results
    # --------------------------------------------------
    cet_results = {}

    for phi in phi_list:
        G = np.full_like(V_grid, np.nan)
        G = (1 / (n + 1)) * (( (-4*np.pi*N0) / (3 * np.log(1 - phi)) )**(1 / 3) ) * DeltaT * (1 - (DeltaTN ** (n + 1)) / (DeltaT ** (n + 1)) )

        cet_results[phi] = {
            "V": V_grid,
            "G": G
        }

    return cet_results