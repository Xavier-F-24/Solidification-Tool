import numpy as np

from io_utils.analysis_utils import r_squared

def fit_ims_power_laws(ims_results, Wanted_G):

    G = ims_results["G"]
    V = ims_results["V+"]
    R = ims_results["R+"]
    Total_undercooling = ims_results["Total_undercooling"]

    idx = np.argmin(np.abs(G - Wanted_G))

    V = V[idx][0]
    R = R[idx]
    Total_undercooling = Total_undercooling[idx]
    
    mask = np.isfinite(V) & np.isfinite(R)

    V = V[mask]
    R = R[mask]

    #mask = np.isfinite(V) & np.isfinite(R) & np.isfinite(Total_undercooling)
    mask2 = V < V[np.argmin(R)]

    V = V[mask2]
    R = R[mask2]
    Dt = Total_undercooling[mask]
    Dt = Dt[mask2]

    #logV = np.log10(V)
    logV = np.log10(V)
    logR = np.log10(R)
    logDt = np.log10(Dt)

    # --------------------------------------------------
    # Radius fit: R = α1 V^β1
    # --------------------------------------------------
    beta1, log_alpha1 = np.polyfit(logV, logR, 1)
    alpha1 = 10 ** log_alpha1

    logR_fit = log_alpha1 + beta1 * logV
    R2_radius = r_squared(logR, logR_fit)

    # --------------------------------------------------
    # Undercooling fit: ΔT = α2 V^β2
    # --------------------------------------------------
    beta2, log_alpha2 = np.polyfit(logV, logDt, 1)
    alpha2 = 10 ** log_alpha2

    logDt_fit = log_alpha2 + beta2 * logV
    R2_undercooling = r_squared(logDt, logDt_fit)

    return {
        "alpha1": alpha1,
        "beta1": beta1,
        "R2_radius": R2_radius,
        "alpha2": alpha2,
        "beta2": beta2,
        "R2_undercooling": R2_undercooling,
    }
    #return alpha1, beta1, alpha2, beta2, R2_radius, R2_undercooling