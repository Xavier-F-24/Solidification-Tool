"""
Results display and visualization panels.
"""

import numpy as np
import streamlit as st


FIT_WARNING_R2 = 0.98


def _settings_table(results):
    settings = results.metadata.get("engine_settings", {})
    if not settings:
        st.info("No engine settings metadata was saved with this run.")
        return
    st.json(settings)


def _finite_range(values):
    finite = np.asarray(values)[np.isfinite(values)]
    if finite.size == 0:
        return None
    return np.nanmin(finite), np.nanmax(finite)


def display_results_tab(results_dict):
    """Main results tab with all figures."""
    col1, col2 = st.columns([4, 1])

    with col1:
        st.header("Simulation Results")
    with col2:
        if st.button("Refresh", use_container_width=False):
            st.rerun()

    figs = results_dict.get("figs", {})
    if not figs:
        st.warning("No results to display. Click 'Run Simulation' to start.")
        return

    st.write("---")

    if "heat_transfer" in figs and results_dict.get("show_heat_transfer"):
        st.subheader("Heat Transfer (G-V Diagram)")
        for fig in figs["heat_transfer"]:
            st.pyplot(fig, use_container_width=True)
        st.caption("Thermal gradient vs. solidification velocity relationship.")

    st.write("---")

    if "ims" in figs and results_dict.get("show_ims"):
        st.subheader("IMS Model Results")
        fig_list = figs["ims"]
        cols = st.columns(len(fig_list) if len(fig_list) <= 2 else 2)
        for i, fig in enumerate(fig_list):
            with cols[i % len(cols)]:
                st.pyplot(fig, use_container_width=True)
        st.caption("Undercooling and tip radius vs. velocity.")

    st.write("---")

    if "ims_fits" in figs and results_dict.get("show_ims_fits"):
        st.subheader("IMS Power Law Fits")
        fig_list = figs["ims_fits"]
        cols = st.columns(len(fig_list) if len(fig_list) <= 2 else 2)
        for i, fig in enumerate(fig_list):
            with cols[i % len(cols)]:
                st.pyplot(fig, use_container_width=True)
        st.caption("Power-law fits at the selected thermal gradient.")

    st.write("---")

    if "pdas_sdas" in figs and (results_dict.get("show_pdas") or results_dict.get("show_sdas")):
        st.subheader("PDAS/SDAS Stability Map")
        for fig in figs["pdas_sdas"]:
            st.pyplot(fig, use_container_width=True)
        show_modes = []
        if results_dict.get("show_pdas"):
            show_modes.append("PDAS")
        if results_dict.get("show_sdas"):
            show_modes.append("SDAS")
        st.caption(f"Primary/secondary dendrite arm spacing stability ({', '.join(show_modes)}).")

    st.write("---")

    if "cet" in figs and results_dict.get("show_cet"):
        st.subheader("Columnar-to-Equiaxed Transition (CET)")
        for fig in figs["cet"]:
            st.pyplot(fig, use_container_width=True)
        st.caption("CET boundaries for selected solid fractions.")


def display_physics_tab(results_dict):
    """Physics results tab with key metrics and numerical diagnostics."""
    st.header("Physics Summary")

    results = results_dict.get("results")
    if results is None:
        st.warning("No results to display.")
        return

    with st.expander("IMS Diagnostics", expanded=True):
        ims = results.ims
        stable_region = ims["Stable"]
        g_values = ims["G"]
        valid_g_mask = np.any(stable_region, axis=1)
        valid_count = int(np.count_nonzero(stable_region))

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Sampling mode", ims.get("sampling_mode", "legacy"))
        with col2:
            st.metric("Stable points", f"{valid_count:,}")
        with col3:
            st.metric("Pe shape", str(ims["Pe"].shape))
        with col4:
            st.metric("Valid G rows", f"{np.count_nonzero(valid_g_mask)}/{len(g_values)}")

        if np.any(valid_g_mask):
            g_min = g_values[valid_g_mask][0]
            g_max = g_values[valid_g_mask][-1]
            st.write(f"**Stable G coverage:** {g_min:.2e} to {g_max:.2e} K/m")

        r_range = _finite_range(results.ims["R+"])
        if r_range:
            st.write(f"**Tip radius R+ range:** {r_range[0]:.2e} to {r_range[1]:.2e} m")

        pe_bounds = ims.get("Pe_bounds")
        if pe_bounds is not None:
            finite_bounds = pe_bounds[np.isfinite(pe_bounds[:, 0])]
            if len(finite_bounds) > 0:
                st.write(
                    "**Adaptive Pe bounds:** "
                    f"{np.nanmin(finite_bounds[:, 0]):.2e} to {np.nanmax(finite_bounds[:, 1]):.2e}"
                )

    with st.expander("Stability Boundaries", expanded=True):
        col1, col2, col3 = st.columns(3)

        V_planar = results.stability["V_planar"]
        V_dend = results.stability["V_dend"]
        G_out = results.stability["G_out"]

        with col1:
            st.metric("G rows", f"{len(G_out)}")
        with col2:
            st.metric("Planar V range", f"{np.min(V_planar):.2e} to {np.max(V_planar):.2e} m/s")
        with col3:
            st.metric("Dendritic V range", f"{np.min(V_dend):.2e} to {np.max(V_dend):.2e} m/s")

    with st.expander("Power Law Fits", expanded=True):
        fit_ims = results.fit_ims

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Radius fit:** R(V) = alpha1 * V^beta1")
            st.metric("alpha1", f"{fit_ims['alpha1']:.4e}")
            st.metric("beta1", f"{fit_ims['beta1']:.4f}")
            st.metric("R^2 radius", f"{fit_ims['R2_radius']:.4f}")
        with col2:
            st.write("**Undercooling fit:** DeltaT(V) = alpha2 * V^beta2")
            st.metric("alpha2", f"{fit_ims['alpha2']:.4e}")
            st.metric("beta2", f"{fit_ims['beta2']:.4f}")
            st.metric("R^2 undercooling", f"{fit_ims['R2_undercooling']:.4f}")

        if fit_ims["R2_radius"] < FIT_WARNING_R2 or fit_ims["R2_undercooling"] < FIT_WARNING_R2:
            st.warning("One or more IMS fit R^2 values are below 0.98. Treat derived spacing/CET trends carefully.")

    with st.expander("Dendrite Arm Spacing (PDAS/SDAS)", expanded=False):
        pdas_spacings = sorted(results.pdas.keys())
        sdas_spacings = sorted(results.sdas.keys())
        st.write(f"**PDAS spacing range:** {pdas_spacings[0] * 1e6:.2e} to {pdas_spacings[-1] * 1e6:.2e} um")
        st.write(f"**SDAS spacing range:** {sdas_spacings[0] * 1e6:.2e} to {sdas_spacings[-1] * 1e6:.2e} um")

    with st.expander("Columnar-to-Equiaxed Transition (CET)", expanded=False):
        phi_list = results_dict.get("phi_list", [0.01, 0.5])
        cet_results = results.cet

        for phi in phi_list:
            st.write(f"**phi = {phi} solid fraction**")
            V = cet_results[phi]["V"]
            G = cet_results[phi]["G"]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"G_min at phi={phi}", f"{np.nanmin(G):.2e} K/m")
            with col2:
                st.metric("V at G_min", f"{V[np.nanargmin(G)]:.2e} m/s")
            with col3:
                st.metric(f"G_max at phi={phi}", f"{np.nanmax(G):.2e} K/m")

    with st.expander("Engine Settings Used", expanded=False):
        _settings_table(results)


def display_data_tab(results_dict):
    """Data export tab with raw values and tables."""
    st.header("Data Export")

    results = results_dict.get("results")
    if results is None:
        st.warning("No results to display.")
        return

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Heat Transfer", "IMS", "PDAS/SDAS", "CET", "Settings"])

    with tab1:
        st.subheader("Heat Transfer Data")
        import pandas as pd

        df = pd.DataFrame({"V (m/s)": results.V, "G (K/m)": results.G})
        st.dataframe(df, use_container_width=True, height=400)
        st.download_button("Download as CSV", df.to_csv(index=False), "heat_transfer.csv", "text/csv")

    with tab2:
        st.subheader("IMS Model Results")

        ims = results.ims
        st.write(f"**Sampling mode:** {ims.get('sampling_mode', 'legacy')}")
        st.write(f"**G values:** {ims['G'].shape[0]} points")
        st.write(f"**Peclet number Pe:** {ims['Pe'].shape}")
        st.write(f"**Tip radius R+:** {ims['R+'].shape}")
        st.write(f"**Dendrite velocity V+:** {ims['V+'].shape}")
        st.write(f"**Total undercooling:** {ims['Total_undercooling'].shape}")
        st.write(f"**Stable points:** {int(np.count_nonzero(ims['Stable'])):,}")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**G values sample:**")
            st.write(ims["G"][:10])
        with col2:
            st.write("**Pe range:**")
            st.write(f"Min: {np.nanmin(ims['Pe']):.2e}, Max: {np.nanmax(ims['Pe']):.2e}")

    with tab3:
        st.subheader("PDAS & SDAS Data")
        import pandas as pd

        summary_data = []
        for spacing in sorted(results.pdas.keys()):
            spacing_um = spacing * 1e6
            pdas_v_range = (np.min(results.pdas[spacing]["V"]), np.max(results.pdas[spacing]["V"]))
            sdas_v_range = (np.min(results.sdas[spacing]["V"]), np.max(results.sdas[spacing]["V"]))

            summary_data.append(
                {
                    "Spacing (um)": f"{spacing_um:.2e}",
                    "PDAS V_min (m/s)": f"{pdas_v_range[0]:.2e}",
                    "PDAS V_max (m/s)": f"{pdas_v_range[1]:.2e}",
                    "SDAS V_min (m/s)": f"{sdas_v_range[0]:.2e}",
                    "SDAS V_max (m/s)": f"{sdas_v_range[1]:.2e}",
                }
            )

        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

    with tab4:
        st.subheader("CET (Columnar-to-Equiaxed Transition)")
        import pandas as pd

        for phi in results_dict.get("phi_list", [0.01, 0.5]):
            st.write(f"**phi = {phi}**")
            df = pd.DataFrame({"V (m/s)": results.cet[phi]["V"], "G (K/m)": results.cet[phi]["G"]})
            st.dataframe(df, use_container_width=True, height=300)
            st.download_button(
                f"Download CET phi={phi}",
                df.to_csv(index=False),
                f"cet_phi_{phi}.csv",
                "text/csv",
                key=f"cet_download_{phi}",
            )

    with tab5:
        st.subheader("Engine Settings")
        _settings_table(results)


def display_help_tab():
    """Help and documentation tab."""
    st.header("Help & Documentation")

    with st.expander("What is this tool?", expanded=True):
        st.write(
            """
            This is a directional solidification simulator based on the MTGN 4XX course
            at Colorado School of Mines. It couples heat transfer, IMS stability,
            dendrite arm spacing, and CET models to predict microstructure evolution.
            """
        )

    with st.expander("Heat Transfer Model"):
        st.write(
            """
            **Steady-state directional solidification**

            Computes the thermal gradient G as a function of solidification velocity V.
            """
        )

    with st.expander("IMS (Ivantsov Multiple Solutes)"):
        st.write(
            """
            **Multi-element undercooling model**

            Solves the marginal stability criterion for dendritic growth in alloys with
            multiple solutes. Legacy mode uses the historical global Pe grid. Adaptive
            mode narrows each G row to its discriminant-valid Pe window.
            """
        )

    with st.expander("Tips & Best Practices"):
        st.write(
            """
            1. Start with a preset alloy.
            2. Adjust one parameter group at a time.
            3. Check the Physics tab for fit quality and stability coverage.
            4. Use adaptive IMS mode for focused Pe sampling comparisons.
            5. Export data for follow-up analysis in Python or spreadsheets.
            """
        )
