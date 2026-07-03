"""
Caching layer for solidification simulator.
Implements multi-stage caching to avoid recomputation.
"""

import streamlit as st
import hashlib
import json
from typing import Dict, Any, Tuple
import numpy as np


def hash_inputs(inputs_dict: Dict[str, Any]) -> str:
    """
    Create a deterministic hash of input parameters.
    Used as cache key to detect when inputs change.
    """
    # Convert to JSON for hashing (handles lists, floats, etc.)
    json_str = json.dumps(inputs_dict, sort_keys=True, default=str)
    return hashlib.md5(json_str.encode()).hexdigest()


def get_or_run_heat_transfer(inputs):
    """
    Cached heat transfer solver.
    Only recomputes if inputs change.
    """
    from solidification_tool.core.pipeline import get_heat_transfer
    
    @st.cache_data(show_spinner="Computing heat transfer...")
    def _solve(inputs_hash: str):
        # We pass the hash, but compute with original inputs
        # The hash ensures cache invalidation when inputs change
        return get_heat_transfer(inputs)
    
    inputs_hash = hash_inputs({
        "k_l": inputs.k_l,
        "rho_s": inputs.rho_s,
        "c_p": inputs.c_p,
        "L_f": inputs.L_f,
        "T_f": inputs.T_f,
        "T_o": inputs.T_o,
    })
    
    # Store in session state for later reference
    if "last_heat_transfer_hash" not in st.session_state:
        st.session_state.last_heat_transfer_hash = None
    
    if st.session_state.last_heat_transfer_hash != inputs_hash:
        st.session_state.last_heat_transfer_hash = inputs_hash
        # Force recompute by changing the hash
        V, G = _solve(inputs_hash)
        st.session_state.V = V
        st.session_state.G = G
    
    return st.session_state.V, st.session_state.G


def get_or_run_ims(inputs, V, G):
    """
    Cached IMS solver.
    Depends on composition and alloy parameters.
    """
    from solidification_tool.core.pipeline import get_ims
    
    @st.cache_data(show_spinner="Solving IMS model...")
    def _solve(inputs_hash: str):
        return get_ims(inputs)
    
    inputs_hash = hash_inputs({
        "C_0": str(inputs.C_0),
        "C_f": str(inputs.C_f),
        "k": str(inputs.k),
        "m": str(inputs.m),
        "D": str(inputs.D),
        "Gamma": inputs.Gamma,
    })
    
    if "last_ims_hash" not in st.session_state:
        st.session_state.last_ims_hash = None
    
    if st.session_state.last_ims_hash != inputs_hash:
        st.session_state.last_ims_hash = inputs_hash
        ims_results = _solve(inputs_hash)
        st.session_state.ims_results = ims_results
    
    return st.session_state.ims_results


def get_or_run_stability_and_fits(inputs, ims_results, wanted_g):
    """
    Cached stability extraction and power law fitting.
    """
    from solidification_tool.core.pipeline import (
        extract_stability_boundaries,
        get_ims_power_laws
    )
    
    @st.cache_data(show_spinner="Extracting stability boundaries...")
    def _solve(inputs_hash: str):
        G_out, V_planar, V_dend = extract_stability_boundaries(ims_results)
        fit_ims_results = get_ims_power_laws(ims_results, wanted_g)
        return G_out, V_planar, V_dend, fit_ims_results
    
    inputs_hash = hash_inputs({
        "ims_valid": str(ims_results.get("Stable", [])),
        "wanted_g": wanted_g,
    })
    
    if "last_stability_hash" not in st.session_state:
        st.session_state.last_stability_hash = None
    
    if st.session_state.last_stability_hash != inputs_hash:
        st.session_state.last_stability_hash = inputs_hash
        G_out, V_planar, V_dend, fit_ims_results = _solve(inputs_hash)
        st.session_state.G_out = G_out
        st.session_state.V_planar = V_planar
        st.session_state.V_dend = V_dend
        st.session_state.fit_ims_results = fit_ims_results
    
    return (
        st.session_state.G_out,
        st.session_state.V_planar,
        st.session_state.V_dend,
        st.session_state.fit_ims_results
    )


def get_or_run_pdas(inputs, V_planar, V_dend, fit_ims_results):
    """
    Cached PDAS solver.
    """
    from solidification_tool.core.pipeline import get_pdas
    
    @st.cache_data(show_spinner="Computing PDAS...")
    def _solve(inputs_hash: str):
        return get_pdas(inputs, V_planar, V_dend, fit_ims_results)
    
    inputs_hash = hash_inputs({
        "NonEq_Freezing_range": inputs.NonEq_Freezing_range,
        "V_planar_range": (float(np.min(V_planar)), float(np.max(V_planar))),
        "fit_ims_hash": str(fit_ims_results),
    })
    
    if "last_pdas_hash" not in st.session_state:
        st.session_state.last_pdas_hash = None
    
    if st.session_state.last_pdas_hash != inputs_hash:
        st.session_state.last_pdas_hash = inputs_hash
        pdas_results = _solve(inputs_hash)
        st.session_state.pdas_results = pdas_results
    
    return st.session_state.pdas_results


def get_or_run_sdas(inputs, V_planar, V_dend):
    """
    Cached SDAS solver.
    """
    from solidification_tool.core.pipeline import get_sdas
    
    @st.cache_data(show_spinner="Computing SDAS...")
    def _solve(inputs_hash: str):
        return get_sdas(inputs, V_planar, V_dend)
    
    inputs_hash = hash_inputs({
        "C_0": str(inputs.C_0),
        "C_f": str(inputs.C_f),
        "k": str(inputs.k),
        "m": str(inputs.m),
        "D": str(inputs.D),
        "Gamma": inputs.Gamma,
        "NonEq_Freezing_range": inputs.NonEq_Freezing_range,
        "V_range": (float(np.min(V_planar)), float(np.max(V_dend))),
    })
    
    if "last_sdas_hash" not in st.session_state:
        st.session_state.last_sdas_hash = None
    
    if st.session_state.last_sdas_hash != inputs_hash:
        st.session_state.last_sdas_hash = inputs_hash
        sdas_results = _solve(inputs_hash)
        st.session_state.sdas_results = sdas_results
    
    return st.session_state.sdas_results


def get_or_run_cet(inputs, fit_ims_results, V_planar, V_dend, G_out):
    """
    Cached CET solver.
    """
    from solidification_tool.core.pipeline import get_cet
    
    @st.cache_data(show_spinner="Computing CET...")
    def _solve(inputs_hash: str):
        return get_cet(inputs, fit_ims_results, V_planar, V_dend, G_out)
    
    inputs_hash = hash_inputs({
        "N0": inputs.N0,
        "DeltaTN": inputs.DeltaTN,
        "fit_ims_hash": str(fit_ims_results),
        "G_out_range": (float(np.min(G_out)), float(np.max(G_out))),
    })
    
    if "last_cet_hash" not in st.session_state:
        st.session_state.last_cet_hash = None
    
    if st.session_state.last_cet_hash != inputs_hash:
        st.session_state.last_cet_hash = inputs_hash
        cet_results, phi_list = _solve(inputs_hash)
        st.session_state.cet_results = cet_results
        st.session_state.phi_list = phi_list
    
    return st.session_state.cet_results, st.session_state.phi_list


def reset_cache():
    """
    Clear all cached results in session state.
    Call this when user clicks 'Reset' or 'New Simulation'.
    """
    cache_keys = [
        "last_heat_transfer_hash",
        "last_ims_hash",
        "last_stability_hash",
        "last_pdas_hash",
        "last_sdas_hash",
        "last_cet_hash",
        "V", "G",
        "ims_results",
        "G_out", "V_planar", "V_dend", "fit_ims_results",
        "pdas_results",
        "sdas_results",
        "cet_results", "phi_list",
    ]
    
    for key in cache_keys:
        if key in st.session_state:
            del st.session_state[key]
