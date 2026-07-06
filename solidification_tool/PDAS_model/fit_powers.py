import numpy as np

from solidification_tool.core.results import ImsPowerLawFit
from solidification_tool.core.validation import EngineComputationError
from solidification_tool.io_utils.analysis_utils import r_squared


def _require_fit_domain(V, R, Dt):
    mask = np.isfinite(V) & np.isfinite(R) & np.isfinite(Dt) & (V > 0) & (R > 0) & (Dt > 0)
    V = V[mask]
    R = R[mask]
    Dt = Dt[mask]

    if len(V) < 3:
        raise EngineComputationError("IMS power-law fit requires at least three finite positive points.")

    tip_idx = np.argmin(R)
    pre_tip = V < V[tip_idx]
    V = V[pre_tip]
    R = R[pre_tip]
    Dt = Dt[pre_tip]

    if len(V) < 3:
        raise EngineComputationError(
            "IMS power-law fit has too few points before the minimum-radius dendritic branch."
        )

    return V, R, Dt


def fit_ims_power_laws(ims_results, Wanted_G):
    G = ims_results["G"]
    V = ims_results["V+"]
    R = ims_results["R+"]
    total_undercooling = ims_results["Total_undercooling"]

    idx = np.argmin(np.abs(G - Wanted_G))

    V = V[idx][0]
    R = R[idx]
    Dt = total_undercooling[idx]
    V, R, Dt = _require_fit_domain(V, R, Dt)

    logV = np.log10(V)
    logR = np.log10(R)
    logDt = np.log10(Dt)

    beta1, log_alpha1 = np.polyfit(logV, logR, 1)
    alpha1 = 10 ** log_alpha1
    logR_fit = log_alpha1 + beta1 * logV
    R2_radius = r_squared(logR, logR_fit)

    beta2, log_alpha2 = np.polyfit(logV, logDt, 1)
    alpha2 = 10 ** log_alpha2
    logDt_fit = log_alpha2 + beta2 * logV
    R2_undercooling = r_squared(logDt, logDt_fit)

    return ImsPowerLawFit(
        alpha1=alpha1,
        beta1=beta1,
        R2_radius=R2_radius,
        alpha2=alpha2,
        beta2=beta2,
        R2_undercooling=R2_undercooling,
    )
