import numpy as np

def extract_stability_boundaries(ims_results):
    """
    Extract planar and dendritic stability boundaries from IMS results.

    Returns:
        G_valid        : (n,) gradients with valid solutions
        V_planar       : (n,) planar -> cellular boundary
        V_dendritic    : (n,) cellular -> dendritic boundary
    """
    G = ims_results["G"]
    V_plus = ims_results["V+"]
    R_plus = ims_results["R+"]

    V_planar = []
    V_dend   = []
    G_out    = []

    for i in range(len(G)):
        V_i = V_plus[i][0]
        R_i = R_plus[i]

        mask = np.isfinite(V_i) & np.isfinite(R_i)
        if not np.any(mask):
            continue

        V_valid = V_i[mask]
        R_valid = R_i[mask]

        # Planar -> cellular: lowest velocity
        V_planar_i = np.min(V_valid)

        # Cellular -> dendritic: smallest tip radius
        idx_min_R  = np.argmin(R_valid)
        V_dend_i   = V_valid[idx_min_R]

        V_planar.append(V_planar_i)
        V_dend.append(V_dend_i)
        G_out.append(G[i])

    return (
        np.array(G_out),
        np.array(V_planar),
        np.array(V_dend),
    )
