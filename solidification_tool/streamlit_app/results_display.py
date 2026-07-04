"""
Results display and visualization panels.
"""

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import time


def display_results_tab(results_dict):
    """
    Main results tab with all figures.
    """
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.header("📈 Simulation Results")
    with col2:
        if st.button("🔄 Refresh", use_container_width=False):
            st.rerun()
    
    # Get the list of figures
    figs = results_dict.get("figs", {})
    
    if not figs:
        st.warning("No results to display. Click 'Run Simulation' to start.")
        return
    
    # Display each figure
    st.write("---")
    
    # Heat Transfer
    if "heat_transfer" in figs and results_dict.get("show_heat_transfer"):
        st.subheader("🔥 Heat Transfer (G-V Diagram)")
        fig_list = figs["heat_transfer"]
        for i, fig in enumerate(fig_list):
            st.pyplot(fig, use_container_width=True)
        st.caption("Thermal gradient vs. solidification velocity relationship")
    
    st.write("---")
    
    # IMS Results
    if "ims" in figs and results_dict.get("show_ims"):
        st.subheader("📊 IMS Model Results")
        fig_list = figs["ims"]
        cols = st.columns(len(fig_list) if len(fig_list) <= 2 else 2)
        for i, fig in enumerate(fig_list):
            with cols[i % len(cols)]:
                st.pyplot(fig, use_container_width=True)
        st.caption("Undercooling and tip radius vs. velocity")
    
    st.write("---")
    
    # IMS Fits
    if "ims_fits" in figs and results_dict.get("show_ims_fits"):
        st.subheader("📈 IMS Power Law Fits")
        fig_list = figs["ims_fits"]
        cols = st.columns(len(fig_list) if len(fig_list) <= 2 else 2)
        for i, fig in enumerate(fig_list):
            with cols[i % len(cols)]:
                st.pyplot(fig, use_container_width=True)
        st.caption(f"Power law fits at desired thermal gradient")
    
    st.write("---")
    
    # PDAS/SDAS
    if "pdas_sdas" in figs and (results_dict.get("show_pdas") or results_dict.get("show_sdas")):
        st.subheader("🔬 PDAS/SDAS Stability Map")
        fig_list = figs["pdas_sdas"]
        for fig in fig_list:
            st.pyplot(fig, use_container_width=True)
        show_modes = []
        if results_dict.get("show_pdas"):
            show_modes.append("PDAS")
        if results_dict.get("show_sdas"):
            show_modes.append("SDAS")
        st.caption(f"Primary/secondary dendrite arm spacing stability ({', '.join(show_modes)})")
    
    st.write("---")
    
    # CET
    if "cet" in figs and results_dict.get("show_cet"):
        st.subheader("⚗️ Columnar-to-Equiaxed Transition (CET)")
        fig_list = figs["cet"]
        for fig in fig_list:
            st.pyplot(fig, use_container_width=True)
        st.caption("CET boundaries for different solid fractions (φ = 0.01 and φ = 0.50)")


def display_physics_tab(results_dict):
    """
    Physics results tab with key metrics.
    """
    st.header("🔬 Physics Summary")
    
    results = results_dict.get("results")
    if results is None:
        st.warning("No results to display.")
        return
    
    # IMS Metrics
    with st.expander("📊 Ivantsov Multiple Solutes (IMS)", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        ims_results = results.ims
        stable_region = ims_results["Stable"]
        G_range = ims_results["G"]
        
        with col1:
            g_min = G_range[np.any(stable_region, axis=1)][0] if np.any(stable_region) else 0
            st.metric("G_min (stability)", f"{g_min:.2e} K/m")
        
        with col2:
            g_max = G_range[np.any(stable_region, axis=1)][-1] if np.any(stable_region) else 0
            st.metric("G_max (stability)", f"{g_max:.2e} K/m")
        
        with col3:
            R_range = np.nanmin(results.ims["R+"]), np.nanmax(results.ims["R+"])
            st.metric("Tip radius range", f"{R_range[0]:.2e} to {R_range[1]:.2e} m")
    
    # Stability Boundaries
    with st.expander("🎯 Stability Boundaries", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        V_planar = results.stability["V_planar"]
        V_dend = results.stability["V_dend"]
        G_out = results.stability["G_out"]
        
        with col1:
            st.metric("Planar V min", f"{np.min(V_planar):.2e} m/s")
        with col2:
            st.metric("Planar V max", f"{np.max(V_planar):.2e} m/s")
        with col3:
            st.metric("Dendritic V range", f"{np.min(V_dend):.2e} to {np.max(V_dend):.2e} m/s")
    
    # Power Law Fits
    with st.expander("📈 Power Law Fits", expanded=False):
        fit_ims = results.fit_ims
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Radius Fit: R(V) = α₁ × V^β₁**")
            st.metric("α₁", f"{fit_ims['alpha1']:.4e}")
            st.metric("β₁", f"{fit_ims['beta1']:.4f}")
        
        with col2:
            st.write("**Undercooling Fit: ΔT(V) = α₂ × V^β₂**")
            st.metric("α₂", f"{fit_ims['alpha2']:.4e}")
            st.metric("β₂", f"{fit_ims['beta2']:.4f}")
    
    # PDAS/SDAS Ranges
    with st.expander("🔬 Dendrite Arm Spacing (PDAS/SDAS)", expanded=False):
        st.write("**PDAS (Primary Dendrite Arm Spacing):**")
        st.write(f"Range: 1 µm to 1 mm (13 logarithmically-spaced values)")
        
        st.write("**SDAS (Secondary Dendrite Arm Spacing):**")
        st.write(f"Range: 1 µm to 1 mm (13 logarithmically-spaced values)")
    
    # CET
    with st.expander("⚗️ Columnar-to-Equiaxed Transition (CET)", expanded=False):
        phi_list = results_dict.get("phi_list", [0.01, 0.5])
        cet_results = results.cet
        
        for phi in phi_list:
            st.write(f"**φ = {phi} (Solid Fraction)**")
            V = cet_results[phi]["V"]
            G = cet_results[phi]["G"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"G_min @ φ={phi}", f"{np.nanmin(G):.2e} K/m")
            with col2:
                st.metric(f"V @ G_min", f"{V[np.nanargmin(G)]:.2e} m/s")
            with col3:
                st.metric(f"G_max @ φ={phi}", f"{np.nanmax(G):.2e} K/m")


def display_data_tab(results_dict):
    """
    Data export tab with raw values and tables.
    """
    st.header("📊 Data Export")
    
    results = results_dict.get("results")
    if results is None:
        st.warning("No results to display.")
        return
    
    # Tab selector for different data views
    tab1, tab2, tab3, tab4 = st.tabs(["Heat Transfer", "IMS", "PDAS/SDAS", "CET"])
    
    # Heat Transfer Data
    with tab1:
        st.subheader("Heat Transfer Data")
        import pandas as pd
        
        V = results.V
        G = results.G
        df = pd.DataFrame({
            "V (m/s)": V,
            "G (K/m)": G
        })
        
        st.dataframe(df, use_container_width=True, height=400)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download as CSV",
            csv,
            "heat_transfer.csv",
            "text/csv"
        )
    
    # IMS Data
    with tab2:
        st.subheader("IMS Model Results")
        
        ims = results.ims
        st.write(f"**G values:** {ims['G'].shape[0]} points")
        st.write(f"**Peclet number (Pe):** {ims['Pe'].shape}")
        st.write(f"**Tip radius (R⁺):** {ims['R+'].shape}")
        st.write(f"**Dendrite velocity (V⁺):** {ims['V+'].shape}")
        st.write(f"**Total undercooling:** {ims['Total_undercooling'].shape}")
        
        # Show sample of G and Pe
        col1, col2 = st.columns(2)
        with col1:
            st.write("**G values (sample):**")
            st.write(ims["G"][:10])
        with col2:
            st.write("**Pe range:**")
            st.write(f"Min: {np.nanmin(ims['Pe']):.2e}, Max: {np.nanmax(ims['Pe']):.2e}")
    
    # PDAS/SDAS Data
    with tab3:
        st.subheader("PDAS & SDAS Data")
        
        import pandas as pd
        
        pdas = results.pdas
        sdas = results.sdas
        
        # Create summary dataframe
        spacings = sorted(list(pdas.keys()))
        summary_data = []
        
        for spacing in spacings:
            spacing_um = spacing * 1e6  # Convert to micrometers
            pdas_v_range = (np.min(pdas[spacing]["V"]), np.max(pdas[spacing]["V"]))
            sdas_v_range = (np.min(sdas[spacing]["V"]), np.max(sdas[spacing]["V"]))
            
            summary_data.append({
                "Spacing (µm)": f"{spacing_um:.2e}",
                "PDAS V_min (m/s)": f"{pdas_v_range[0]:.2e}",
                "PDAS V_max (m/s)": f"{pdas_v_range[1]:.2e}",
                "SDAS V_min (m/s)": f"{sdas_v_range[0]:.2e}",
                "SDAS V_max (m/s)": f"{sdas_v_range[1]:.2e}",
            })
        
        df = pd.DataFrame(summary_data)
        st.dataframe(df, use_container_width=True)
    
    # CET Data
    with tab4:
        st.subheader("CET (Columnar-to-Equiaxed Transition)")
        
        import pandas as pd
        
        phi_list = results_dict.get("phi_list", [0.01, 0.5])
        cet = results.cet
        
        for phi in phi_list:
            st.write(f"**φ = {phi}**")
            
            V = cet[phi]["V"]
            G = cet[phi]["G"]
            
            df = pd.DataFrame({
                "V (m/s)": V,
                "G (K/m)": G
            })
            
            st.dataframe(df, use_container_width=True, height=300)
            
            csv = df.to_csv(index=False)
            st.download_button(
                f"📥 Download CET φ={phi}",
                csv,
                f"cet_phi_{phi}.csv",
                "text/csv",
                key=f"cet_download_{phi}"
            )


def display_help_tab():
    """
    Help and documentation tab.
    """
    st.header("📖 Help & Documentation")
    
    with st.expander("🔍 What is this tool?", expanded=True):
        st.write("""
        This is a **directional solidification simulator** based on the MTGN 4XX course
        at Colorado School of Mines. It couples 5 physics models to predict microstructure
        evolution during crystal growth:
        """)
    
    with st.expander("🔥 Heat Transfer Model"):
        st.write("""
        **Steady-State Directional Solidification**
        
        Computes the thermal gradient G as a function of solidification velocity V.
        """)
    
    with st.expander("📊 IMS (Ivantsov Multiple Solutes)"):
        st.write("""
        **Multi-element undercooling model**
        
        Solves the marginal stability criterion for dendritic growth in alloys with
        multiple solutes.
        """)
    
    with st.expander("💡 Tips & Best Practices"):
        st.write("""
        1. **Start with a preset:** Choose a known alloy to get physical insight
        2. **Adjust one parameter at a time:** Easier to see the effect
        3. **Check the Physics tab:** Verify results are reasonable
        4. **Export data:** Use the Data tab to analyze in Excel/Python
        5. **Compare:** Run multiple simulations and compare results
        """)
