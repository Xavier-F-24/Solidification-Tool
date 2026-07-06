"""
Ivantsov multiple-solute undercooling model.
"""

import numpy as np
from scipy.optimize import brentq

from solidification_tool.IMS_model.ivantsov import Ivantsov
from solidification_tool.core.results import ImsResults
from solidification_tool.core.settings import EngineSettings
from solidification_tool.core.validation import EngineComputationError


def _compute_solutal_stability_term(C_0, k, m, Pe):
    """Return liquid composition response and the solutal stability term."""
    Iv = Ivantsov(Pe)

    k3 = k[None, :, :]
    m3 = m[None, :, :]
    C03 = C_0[None, :, :]

    eta = 1 - (2 * k3) / (
        2 * k3 - 1 + np.sqrt(1 + (2 * np.pi / Pe) ** 2)
    )
    c_l_star = C03 / (1 - (1 - k3) * Iv)
    s_term = m3 * Pe * (1 - k3) * c_l_star * eta

    return c_l_star, s_term


def _legacy_peclet_grid(D, settings: EngineSettings):
    """Construct the original solute-scaled Peclet grid."""
    p_base = np.logspace(settings.ims_pe_min_exp, settings.ims_pe_max_exp, settings.ims_pe_count)
    d_ref = D[0, 0]
    scale = d_ref / D
    pe = scale * p_base[None, :]
    return p_base, pe[None, :, :], None


def _discriminant_for_base_peclet(p_base, C_0, k, m, D, Gamma, G_value):
    p_base = np.atleast_1d(p_base).astype(float)
    d_ref = D[0, 0]
    scale = d_ref / D
    pe = scale * p_base[None, :]
    pe = pe[None, :, :]

    _, s_term = _compute_solutal_stability_term(C_0, k, m, pe)
    a_term = 4 * np.pi**2 * Gamma
    b_term = 2 * np.sum(s_term, axis=1)
    disc = b_term[0] ** 2 - 4 * a_term * G_value
    return disc[0] if disc.shape == (1,) else disc


def _refine_bound(left_p, right_p, C_0, k, m, D, Gamma, G_value):
    left_disc = _discriminant_for_base_peclet(left_p, C_0, k, m, D, Gamma, G_value)
    right_disc = _discriminant_for_base_peclet(right_p, C_0, k, m, D, Gamma, G_value)

    if left_disc == 0:
        return left_p
    if right_disc == 0:
        return right_p
    if np.sign(left_disc) == np.sign(right_disc):
        return right_p if right_disc > 0 else left_p

    return brentq(
        lambda p: _discriminant_for_base_peclet(p, C_0, k, m, D, Gamma, G_value),
        left_p,
        right_p,
        xtol=1e-14,
        rtol=1e-12,
        maxiter=100,
    )


def _refined_valid_bounds(p_probe, row_valid, C_0, k, m, D, Gamma, G_value):
    valid_idx = np.flatnonzero(row_valid)
    first = valid_idx[0]
    last = valid_idx[-1]

    if first == 0:
        p_min = p_probe[0]
    else:
        p_min = _refine_bound(p_probe[first - 1], p_probe[first], C_0, k, m, D, Gamma, G_value)

    if last == len(p_probe) - 1:
        p_max = p_probe[-1]
    else:
        p_max = _refine_bound(p_probe[last], p_probe[last + 1], C_0, k, m, D, Gamma, G_value)

    return p_min, p_max


def _adaptive_peclet_grid(C_0, k, m, D, Gamma, G_values, settings: EngineSettings):
    """
    Construct a per-gradient Peclet grid from stability-discriminant windows.

    The marginal-stability quadratic has real roots only when
    B(Pe)^2 - 4*A*G > 0. Adaptive mode probes that discriminant on the legacy
    grid, refines the valid-window edges with scalar root solves, then resamples
    each gradient row while preserving rectangular arrays for downstream consumers.
    """
    p_probe, pe_probe, _ = _legacy_peclet_grid(D, settings)
    _, s_probe = _compute_solutal_stability_term(C_0, k, m, pe_probe)

    a_term = 4 * np.pi**2 * Gamma
    b_probe = 2 * np.sum(s_probe, axis=1)
    disc_probe = b_probe[:, None, :] ** 2 - 4 * a_term * G_values[:, None, None]
    valid_probe = disc_probe[:, 0, :] > 0

    if not np.any(valid_probe):
        raise EngineComputationError(
            "IMS adaptive sampling found no valid Peclet window for the requested G range."
        )

    p_rows = np.empty((len(G_values), settings.ims_pe_count), dtype=float)
    bounds = np.full((len(G_values), 2), np.nan, dtype=float)

    for idx, row_valid in enumerate(valid_probe):
        if np.any(row_valid):
            p_min, p_max = _refined_valid_bounds(
                p_probe,
                row_valid,
                C_0,
                k,
                m,
                D,
                Gamma,
                G_values[idx],
            )
            bounds[idx] = (p_min, p_max)
            if p_min == p_max:
                p_rows[idx] = p_min
            else:
                p_rows[idx] = np.logspace(np.log10(p_min), np.log10(p_max), settings.ims_pe_count)
        else:
            p_rows[idx] = p_probe

    d_ref = D[0, 0]
    scale = (d_ref / D).reshape(1, D.shape[0], 1)
    pe = scale * p_rows[:, None, :]
    return p_rows, pe, bounds


def solve_ims(inputs, settings: EngineSettings | None = None):
    """
    Multi-solute Ivantsov plus marginal-stability solver.

    Axis convention:
        Axis 0 -> thermal gradient G [K/m]
        Axis 1 -> solute index
        Axis 2 -> Peclet number Pe [-]
    """
    settings = settings or EngineSettings()

    C_0 = np.atleast_1d(inputs.C_0).astype(float)[:, None]
    k = np.atleast_1d(inputs.k).astype(float)[:, None]
    m = np.atleast_1d(inputs.m).astype(float)[:, None]
    D = np.atleast_1d(inputs.D).astype(float)[:, None]

    gamma = float(inputs.Gamma)
    g_values = np.logspace(settings.ims_g_min_exp, settings.ims_g_max_exp, settings.ims_g_count)
    G = g_values[:, None, None]

    d_ref = D[0, 0]
    if settings.ims_sampling_mode == "adaptive":
        p_base, Pe, pe_bounds = _adaptive_peclet_grid(C_0, k, m, D, gamma, g_values, settings)
    else:
        p_base, Pe, pe_bounds = _legacy_peclet_grid(D, settings)

    c_l_star, s_term = _compute_solutal_stability_term(C_0, k, m, Pe)

    # Marginal stability quadratic: A/R^2 + B/R + G = 0.
    a_term = 4 * np.pi**2 * gamma
    b_term = 2 * np.sum(s_term, axis=1)
    b_term = b_term[:, None, :]

    disc = b_term**2 - 4 * a_term * G
    valid = disc > 0

    quad_plus = np.full_like(disc, np.nan)
    quad_minus = np.full_like(disc, np.nan)

    sqrt_disc = np.zeros_like(disc)
    sqrt_disc[valid] = np.sqrt(disc[valid])

    quad_plus[valid] = (-b_term + sqrt_disc)[valid] / (2 * a_term)
    quad_minus[valid] = (-b_term - sqrt_disc)[valid] / (2 * a_term)

    R_plus = 1 / quad_plus
    R_minus = 1 / quad_minus

    R_plus = R_plus[:, 0, :]
    R_minus = R_minus[:, 0, :]

    V_plus = 2 * d_ref * Pe / R_plus[:, None, :]
    V_minus = 2 * d_ref * Pe / R_minus[:, None, :]

    m3 = m[None, :, :]
    C03 = C_0[None, :, :]
    solute_undercooling = m3 * (C03 - c_l_star)

    delta_t_solute = np.sum(solute_undercooling, axis=1)
    delta_t_solute = delta_t_solute[:, None, :]

    R_tip = np.minimum(R_plus, R_minus)
    curvature_undercooling = 2 * gamma / R_tip
    total_undercooling = delta_t_solute + curvature_undercooling[:, None, :]
    total_undercooling = total_undercooling[:, 0, :]

    pe_out = Pe[0] if Pe.shape[0] == 1 else Pe
    solute_undercooling_out = (
        solute_undercooling[0] if solute_undercooling.shape[0] == 1 else solute_undercooling
    )

    return ImsResults(
        G=g_values,
        Pe=pe_out,
        P_base=p_base,
        Pe_bounds=pe_bounds,
        Pe_bounds_source="refined_discriminant_roots" if settings.ims_sampling_mode == "adaptive" else None,
        sampling_mode=settings.ims_sampling_mode,
        R_plus=R_plus,
        R_minus=R_minus,
        V_plus=V_plus,
        V_minus=V_minus,
        Total_undercooling=total_undercooling,
        Stable=valid[:, 0, :],
        Solute_undercooling=solute_undercooling_out,
        Curvature_undercooling=curvature_undercooling,
    )
