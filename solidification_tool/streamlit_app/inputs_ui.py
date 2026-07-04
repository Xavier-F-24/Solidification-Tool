"""
Sidebar UI components for input management.
"""

import streamlit as st
import numpy as np
from solidification_tool.core.inputs import SolidificationInputs
from solidification_tool.streamlit_app.config import PRESETS, DEFAULT_VIZ_SETTINGS, DEFAULT_IMS_SETTINGS


def load_preset_into_state(preset_name: str):
    """Load a preset alloy into session state."""
    if preset_name not in PRESETS:
        st.error(f"Preset '{preset_name}' not found!")
        return
    
    preset = PRESETS[preset_name]
    st.session_state.preset_name = preset_name
    
    # Heat transfer
    st.session_state.k_l = preset["heat_transfer"]["k_l"]
    st.session_state.rho_s = preset["heat_transfer"]["rho_s"]
    st.session_state.c_p = preset["heat_transfer"]["c_p"]
    st.session_state.L_f = preset["heat_transfer"]["L_f"]
    st.session_state.T_f = preset["heat_transfer"]["T_f"]
    st.session_state.T_o = preset["heat_transfer"]["T_o"]
    
    # Composition
    st.session_state.C_0 = preset["composition"]["C_0"].copy()
    st.session_state.C_f = preset["composition"]["C_f"].copy()
    st.session_state.k = preset["composition"]["k"].copy()
    st.session_state.m = preset["composition"]["m"].copy()
    st.session_state.D = preset["composition"]["D"].copy()
    st.session_state.Gamma = preset["composition"]["Gamma"]
    
    # Model params
    st.session_state.NonEq_Freezing_range = preset["model_params"]["NonEq_Freezing_range"]
    st.session_state.N0 = preset["model_params"]["N0"]
    st.session_state.DeltaTN = preset["model_params"]["DeltaTN"]


def render_sidebar():
    """Main sidebar UI with all input controls."""
    
    with st.sidebar:
        st.title("⚙️ Settings")
        
        # =====================================================================
        # PRESETS
        # =====================================================================
        st.header("📋 Presets")
        preset_names = list(PRESETS.keys())
        selected_preset = st.selectbox(
            "Choose Alloy Preset",
            preset_names,
            key="preset_selector"
        )
        
        if st.button("Load Preset", use_container_width=True):
            load_preset_into_state(selected_preset)
            st.success(f"✅ Loaded: {selected_preset}")
            st.rerun()
        
        st.divider()
        
        # =====================================================================
        # HEAT TRANSFER PROPERTIES
        # =====================================================================
        with st.expander("🔥 Heat Transfer Properties", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.session_state.k_l = st.number_input(
                    "k_l (W/m-K)",
                    min_value=1.0,
                    max_value=200.0,
                    value=st.session_state.get("k_l", 30.5),
                    step=0.5
                )
                st.session_state.rho_s = st.number_input(
                    "ρ_s (kg/m³)",
                    min_value=1000,
                    max_value=20000,
                    value=st.session_state.get("rho_s", 7850),
                    step=100
                )
                st.session_state.c_p = st.number_input(
                    "c_p (J/kg-K)",
                    min_value=100,
                    max_value=3000,
                    value=st.session_state.get("c_p", 670),
                    step=10
                )
            
            with col2:
                st.session_state.L_f = st.number_input(
                    "L_f (J/kg)",
                    min_value=1e5,
                    max_value=1e6,
                    value=st.session_state.get("L_f", 2.91e5),
                    step=1e4,
                    format="%.2e"
                )
                st.session_state.T_f = st.number_input(
                    "T_f (K)",
                    min_value=500,
                    max_value=3000,
                    value=st.session_state.get("T_f", 1728),
                    step=50
                )
                st.session_state.T_o = st.number_input(
                    "T_o (K)",
                    min_value=100,
                    max_value=1000,
                    value=st.session_state.get("T_o", 500),
                    step=10
                )
        
        st.divider()
        
        # =====================================================================
        # ALLOY COMPOSITION
        # =====================================================================
        with st.expander("🧪 Alloy Composition", expanded=False):
            st.write("**Number of Solutes:**")
            n_solutes = st.number_input(
                "Solutes",
                min_value=1,
                max_value=5,
                value=len(st.session_state.get("C_0", [1.0])),
                key="n_solutes"
            )
            
            # Initialize arrays if needed
            if "C_0" not in st.session_state:
                st.session_state.C_0 = [18.29, 11.55, 1.4]
            if "C_f" not in st.session_state:
                st.session_state.C_f = [24.55, 16.30, 3.33]
            if "k" not in st.session_state:
                st.session_state.k = [1.03, 0.74, 0.75]
            if "m" not in st.session_state:
                st.session_state.m = [1.92, -6.34, -4.14]
            if "D" not in st.session_state:
                st.session_state.D = [8e-9, 8e-9, 8e-8]
            
            # Resize arrays to match n_solutes
            for arr_name in ["C_0", "C_f", "k", "m", "D"]:
                arr = st.session_state[arr_name]
                if len(arr) < n_solutes:
                    arr.extend([arr[-1] if arr else 0.0 for _ in range(n_solutes - len(arr))])
                elif len(arr) > n_solutes:
                    arr = arr[:n_solutes]
                st.session_state[arr_name] = arr
            
            # Input fields for each solute
            for i in range(n_solutes):
                st.write(f"**Solute {i + 1}:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.session_state.C_0[i] = st.number_input(
                        f"C_0[{i}] (wt%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=st.session_state.C_0[i],
                        step=0.1,
                        key=f"C_0_{i}"
                    )
                    st.session_state.k[i] = st.number_input(
                        f"k[{i}] (coeff)",
                        min_value=0.1,
                        max_value=3.0,
                        value=st.session_state.k[i],
                        step=0.01,
                        key=f"k_{i}"
                    )
                    st.session_state.D[i] = st.number_input(
                        f"D[{i}] (m²/s)",
                        min_value=1e-11,
                        max_value=1e-6,
                        value=st.session_state.D[i],
                        step=1e-10,
                        format="%.2e",
                        key=f"D_{i}"
                    )
                
                with col2:
                    st.session_state.C_f[i] = st.number_input(
                        f"C_f[{i}] (wt%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=st.session_state.C_f[i],
                        step=0.1,
                        key=f"C_f_{i}"
                    )
                    st.session_state.m[i] = st.number_input(
                        f"m[{i}] (K/wt%)",
                        min_value=-20.0,
                        max_value=20.0,
                        value=st.session_state.m[i],
                        step=0.01,
                        key=f"m_{i}"
                    )
            
            # Gamma
            st.session_state.Gamma = st.number_input(
                "Γ (Gibbs-Thomson)",
                min_value=1e-10,
                max_value=1e-4,
                value=st.session_state.get("Gamma", 2.56e-7),
                step=1e-9,
                format="%.2e"
            )
        
        st.divider()
        
        # =====================================================================
        # MODEL PARAMETERS
        # =====================================================================
        with st.expander("⚙️ Model Parameters", expanded=False):
            st.session_state.NonEq_Freezing_range = st.slider(
                "NonEq Freezing Range (K)",
                min_value=1,
                max_value=500,
                value=st.session_state.get("NonEq_Freezing_range", 88),
                step=1
            )
            
            st.session_state.N0 = st.number_input(
                "N₀ (nucleants/m³)",
                min_value=1e10,
                max_value=1e14,
                value=st.session_state.get("N0", 1e12),
                step=1e11,
                format="%.2e"
            )
            
            st.session_state.DeltaTN = st.slider(
                "ΔT_N (nucleation undercooling, K)",
                min_value=0.1,
                max_value=10.0,
                value=st.session_state.get("DeltaTN", 2.5),
                step=0.1
            )
        
        st.divider()
        
        # =====================================================================
        # VISUALIZATION OPTIONS
        # =====================================================================
        with st.expander("📊 Visualization Options", expanded=False):
            st.write("**Show Models:**")
            st.session_state.show_heat_transfer = st.checkbox(
                "Heat Transfer (G-V)",
                value=st.session_state.get("show_heat_transfer", True)
            )
            st.session_state.show_ims = st.checkbox(
                "IMS Results",
                value=st.session_state.get("show_ims", True)
            )
            st.session_state.show_ims_fits = st.checkbox(
                "IMS Power Law Fits",
                value=st.session_state.get("show_ims_fits", True)
            )
            st.session_state.show_pdas = st.checkbox(
                "PDAS Curves",
                value=st.session_state.get("show_pdas", True)
            )
            st.session_state.show_sdas = st.checkbox(
                "SDAS Curves",
                value=st.session_state.get("show_sdas", True)
            )
            st.session_state.show_cet = st.checkbox(
                "CET Boundaries",
                value=st.session_state.get("show_cet", True)
            )
        
        st.divider()
        
        # =====================================================================
        # IMS ANALYSIS SETTINGS
        # =====================================================================
        with st.expander("🔬 IMS Analysis", expanded=False):
            st.session_state.wanted_g = st.number_input(
                "Desired G for Power Law Fit (K/m)",
                min_value=1e3,
                max_value=1e6,
                value=st.session_state.get("wanted_g", 1e5),
                step=1e4,
                format="%.2e"
            )
            
            with st.expander("G Range (for IMS plots)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.session_state.g_range_min_exp = st.number_input(
                        "G_min exponent",
                        min_value=-9,
                        max_value=0,
                        value=st.session_state.get("g_range_min_exp", -9),
                        step=1
                    )
                with col2:
                    st.session_state.g_range_max_exp = st.number_input(
                        "G_max exponent",
                        min_value=0,
                        max_value=10,
                        value=st.session_state.get("g_range_max_exp", 9),
                        step=1
                    )


def create_inputs_from_state() -> SolidificationInputs:
    """
    Create a SolidificationInputs dataclass from session state.
    This is called just before running the simulation.
    """
    return SolidificationInputs(
        k_l=st.session_state.get("k_l", 30.5),
        rho_s=st.session_state.get("rho_s", 7850),
        c_p=st.session_state.get("c_p", 670),
        L_f=st.session_state.get("L_f", 2.91e5),
        T_f=st.session_state.get("T_f", 1728),
        T_o=st.session_state.get("T_o", 500),
        C_0=st.session_state.get("C_0", [18.29, 11.55, 1.4]),
        C_f=st.session_state.get("C_f", [24.55, 16.30, 3.33]),
        k=st.session_state.get("k", [1.03, 0.74, 0.75]),
        m=st.session_state.get("m", [1.92, -6.34, -4.14]),
        D=st.session_state.get("D", [8e-9, 8e-9, 8e-8]),
        Gamma=st.session_state.get("Gamma", 2.56e-7),
        NonEq_Freezing_range=st.session_state.get("NonEq_Freezing_range", 88),
        N0=st.session_state.get("N0", 1e12),
        DeltaTN=st.session_state.get("DeltaTN", 2.5),
    )
