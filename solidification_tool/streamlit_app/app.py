"""
Main Streamlit application for the Solidification Simulator.
"""

import os
import sys
import time
import traceback
from datetime import datetime

import numpy as np
import streamlit as st

current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from solidification_tool.app_api import PlotSettings, build_figures
from solidification_tool.streamlit_app.caching import get_or_run_simulation, reset_cache
from solidification_tool.streamlit_app.config import APP_DESCRIPTION, APP_SUBTITLE, APP_TITLE
from solidification_tool.streamlit_app.inputs_ui import (
    create_engine_settings_from_state,
    create_inputs_from_state,
    load_preset_into_state,
    render_sidebar,
)
from solidification_tool.streamlit_app.results_display import (
    display_data_tab,
    display_help_tab,
    display_physics_tab,
    display_results_tab,
)


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="solid",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header {
        text-align: center;
        padding: 20px 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
        margin: 5px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "simulation_complete" not in st.session_state:
    st.session_state.simulation_complete = False
    st.session_state.last_run_time = None
    st.session_state.results = None
    st.session_state.figs = None

if "preset_name" not in st.session_state:
    load_preset_into_state("Fe-Ni-Cr (Baseline)")


col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f"<h1 style='text-align: center;'>{APP_TITLE}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: gray;'>{APP_SUBTITLE}</p>", unsafe_allow_html=True)

st.markdown(APP_DESCRIPTION)
st.divider()

render_sidebar()


def run_simulation():
    """Execute the full simulation pipeline."""
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Preparing inputs...")
        progress_bar.progress(5)
        inputs = create_inputs_from_state()
        engine_settings = create_engine_settings_from_state()

        status_text.text("Running simulation engine...")
        progress_bar.progress(35)
        wanted_g = st.session_state.get("wanted_g", 1e5)
        results = get_or_run_simulation(inputs, wanted_g, engine_settings)

        status_text.text("Generating visualizations...")
        progress_bar.progress(90)
        figs = build_figures(
            results,
            PlotSettings(
                wanted_g=wanted_g,
                show_pdas=st.session_state.get("show_pdas", True),
                show_sdas=st.session_state.get("show_sdas", True),
            ),
        )

        status_text.text("Done.")
        progress_bar.progress(100)
        time.sleep(0.5)
        status_text.empty()
        progress_bar.empty()

        return results, figs

    except Exception as exc:
        st.error(f"Simulation failed: {str(exc)}")
        st.error(traceback.format_exc())
        return None, None


col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("RUN SIMULATION", use_container_width=True, key="run_sim_btn"):
        start_time = time.time()
        results, figs = run_simulation()

        if results is not None and figs is not None:
            elapsed_time = time.time() - start_time

            st.session_state.simulation_complete = True
            st.session_state.results = results
            st.session_state.figs = figs
            st.session_state.last_run_time = elapsed_time

            st.success(f"Simulation complete in {elapsed_time:.2f}s")
            st.rerun()

st.divider()

if st.session_state.simulation_complete:
    results_dict = {
        "results": st.session_state.results,
        "figs": st.session_state.figs,
        "phi_list": st.session_state.results.phi_list,
        "show_heat_transfer": st.session_state.get("show_heat_transfer", True),
        "show_ims": st.session_state.get("show_ims", True),
        "show_ims_fits": st.session_state.get("show_ims_fits", True),
        "show_pdas": st.session_state.get("show_pdas", True),
        "show_sdas": st.session_state.get("show_sdas", True),
        "show_cet": st.session_state.get("show_cet", True),
    }

    tab1, tab2, tab3, tab4 = st.tabs(["Results", "Physics", "Data", "Help"])

    with tab1:
        display_results_tab(results_dict)
    with tab2:
        display_physics_tab(results_dict)
    with tab3:
        display_data_tab(results_dict)
    with tab4:
        display_help_tab()

    st.divider()
    st.subheader("Export Results")

    col1, col2, col3 = st.columns(3)

    with col1:
        import io

        buffer = io.BytesIO()
        np.savez_compressed(
            buffer,
            V=st.session_state.results.V,
            G=st.session_state.results.G,
            ims=st.session_state.results.ims,
            fit_ims=st.session_state.results.fit_ims,
        )
        buffer.seek(0)

        st.download_button(
            "Results (NPZ)",
            buffer.getvalue(),
            f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.npz",
            "application/octet-stream",
            use_container_width=True,
        )

    with col2:
        import json

        inputs_json = json.dumps(st.session_state.results.inputs, indent=2, default=str)
        st.download_button(
            "Inputs (JSON)",
            inputs_json,
            f"inputs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json",
            use_container_width=True,
        )

    with col3:
        if st.button("New Simulation", use_container_width=True):
            reset_cache()
            st.session_state.simulation_complete = False
            st.session_state.results = None
            st.session_state.figs = None
            st.rerun()

else:
    st.info("Adjust parameters in the sidebar, then click **RUN SIMULATION** to start.")
