"""
Main Streamlit application for Solidification Simulator.

MVP Architecture:
1. Sidebar inputs (presets + dynamic controls)
2. Main panel with tabs (Results, Physics, Data, Help)
3. Real-time caching for performance
4. Export functionality (NPZ, JSON, figures)
"""

import sys
import os

# Add the repo root to Python path so imports work
# This handles both local runs and Streamlit Cloud deployment
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import streamlit as st
import time
import traceback
from datetime import datetime
import numpy as np

# Import app modules
from solidification_tool.streamlit_app.config import (
    APP_TITLE,
    APP_SUBTITLE,
    APP_DESCRIPTION,
    FIG_SIZE_DEFAULT,
)
from solidification_tool.streamlit_app.inputs_ui import (
    render_sidebar,
    create_inputs_from_state,
    load_preset_into_state,
)
from solidification_tool.streamlit_app.caching import (
    get_or_run_simulation,
    reset_cache,
)
from solidification_tool.visualization.figures import show_all
from solidification_tool.streamlit_app.results_display import (
    display_results_tab,
    display_physics_tab,
    display_data_tab,
    display_help_tab,
)


# =========================================================================
# PAGE CONFIG
# =========================================================================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
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
    """, unsafe_allow_html=True)

# =========================================================================
# INITIALIZE SESSION STATE
# =========================================================================
if "simulation_complete" not in st.session_state:
    st.session_state.simulation_complete = False
    st.session_state.last_run_time = None
    st.session_state.results = None
    st.session_state.figs = None

# Load default preset on first run
if "preset_name" not in st.session_state:
    load_preset_into_state("Fe-Ni-Cr (Baseline)")


# =========================================================================
# HEADER
# =========================================================================
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f"<h1 style='text-align: center;'>{APP_TITLE}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: gray;'>{APP_SUBTITLE}</p>", unsafe_allow_html=True)

st.markdown(APP_DESCRIPTION)
st.divider()


# =========================================================================
# SIDEBAR
# =========================================================================
render_sidebar()


# =========================================================================
# MAIN PANEL
# =========================================================================
def run_simulation():
    """Execute the full simulation pipeline."""
    try:
        # Progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create inputs from session state
        status_text.text("📋 Preparing inputs...")
        progress_bar.progress(5)
        inputs = create_inputs_from_state()
        
        # Engine
        status_text.text("Running simulation engine...")
        progress_bar.progress(35)
        wanted_g = st.session_state.get("wanted_g", 1e5)
        results = get_or_run_simulation(inputs, wanted_g)
        
        # Generate figures
        status_text.text("Generating visualizations...")
        progress_bar.progress(90)
        show_pdas = st.session_state.get("show_pdas", True)
        show_sdas = st.session_state.get("show_sdas", True)
        
        figs = show_all(
            results,
            Wanted_G=wanted_g,
            show_pdas=show_pdas,
            show_sdas=show_sdas,
            ims_g_range=[]
        )
        
        # Complete
        status_text.text("✅ Done!")
        progress_bar.progress(100)
        time.sleep(0.5)
        status_text.empty()
        progress_bar.empty()
        
        return results, figs
        
    except Exception as e:
        st.error(f"❌ Simulation failed: {str(e)}")
        st.error(traceback.format_exc())
        return None, None


# Main content area
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("⚡ RUN SIMULATION", use_container_width=True, key="run_sim_btn"):
        start_time = time.time()
        results, figs = run_simulation()
        
        if results is not None and figs is not None:
            elapsed_time = time.time() - start_time
            
            st.session_state.simulation_complete = True
            st.session_state.results = results
            st.session_state.figs = figs
            st.session_state.last_run_time = elapsed_time
            
            st.success(f"✅ Simulation complete in {elapsed_time:.2f}s")
            st.rerun()

st.divider()

# Display results if simulation has run
if st.session_state.simulation_complete:
    # Build results dict for display functions
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
    
    # Tab interface
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Results", "🔬 Physics", "📊 Data", "📖 Help"])
    
    with tab1:
        display_results_tab(results_dict)
    
    with tab2:
        display_physics_tab(results_dict)
    
    with tab3:
        display_data_tab(results_dict)
    
    with tab4:
        display_help_tab()
    
    # Download section at bottom
    st.divider()
    st.subheader("💾 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export as NPZ
        import io
        buffer = io.BytesIO()
        
        from solidification_tool.io_utils.results_io import save_results
        # Create a temporary mock run dir
        class MockRunDir:
            pass
        
        # Simplified NPZ export
        np.savez_compressed(
            buffer,
            V=st.session_state.results.V,
            G=st.session_state.results.G,
            ims=st.session_state.results.ims,
            fit_ims=st.session_state.results.fit_ims,
        )
        buffer.seek(0)
        
        st.download_button(
            "📦 Results (NPZ)",
            buffer.getvalue(),
            f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.npz",
            "application/octet-stream",
            use_container_width=True
        )
    
    with col2:
        # Export inputs as JSON
        import json
        inputs_json = json.dumps(st.session_state.results.inputs, indent=2, default=str)
        
        st.download_button(
            "📋 Inputs (JSON)",
            inputs_json,
            f"inputs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json",
            use_container_width=True
        )
    
    with col3:
        # Reset button
        if st.button("🔄 New Simulation", use_container_width=True):
            reset_cache()
            st.session_state.simulation_complete = False
            st.session_state.results = None
            st.session_state.figs = None
            st.rerun()

else:
    st.info("👈 Adjust parameters in the sidebar, then click **⚡ RUN SIMULATION** to start!")
