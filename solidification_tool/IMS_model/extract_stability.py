import numpy as np

from solidification_tool.core.results import ImsResults
from solidification_tool.core.validation import EngineComputationError


def extract_stability_boundaries(ims_results):
    """
    Extract planar and dendritic stability boundaries from IMS results.

    Returns:
        G_valid        : (n,) gradients with valid solutions
        V_planar       : (n,) planar -> cellular boundary
        V_dendritic    : (n,) cellular -> dendritic boundary
    """
    if not isinstance(ims_results, ImsResults):
        ims_results = ImsResults.from_dict(ims_results)

    G = ims_results.G
    V_plus = ims_results.V_plus
    R_plus = ims_results.R_plus

    V_planar = []
    V_dend   = []
    G_out    = []

    for i in range(len(G)):
        V_i = V_plus[i][0]
        R_i = R_plus[i]

        mask = np.isfinite(V_i) & np.isfinite(R_i) & (V_i > 0) & (R_i > 0)
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

    if not G_out:
        raise EngineComputationError("IMS stability extraction found no finite positive stability branch.")

    return (
        np.array(G_out),
        np.array(V_planar),
        np.array(V_dend),
    )
