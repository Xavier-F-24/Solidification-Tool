import numpy as np

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

    logV = np.log10(V)

    # R = α1 V^β1
    beta1, log_alpha1 = np.polyfit(logV, np.log10(R), 1)
    alpha1 = 10**log_alpha1

    # ΔT = α2 V^β2
    beta2, log_alpha2 = np.polyfit(logV, np.log10(Dt), 1)
    alpha2 = 10**log_alpha2

    return alpha1, beta1, alpha2, beta2