from solidification_tool.core.inputs import SolidificationInputs

from solidification_tool.heat_models.steady_state_directional import solve_steady_state_directional
from solidification_tool.heat_visuals.G_V_plots import plot_G_V

from solidification_tool.IMS_model.ims import solve_ims
from solidification_tool.IMS_model.extract_stability import extract_stability_boundaries
from solidification_tool.IMS_visuals.V_R_plots import plot_V_R
from solidification_tool.IMS_visuals.stability_plots import dendritic_stability_edges

from solidification_tool.PDAS_model.fit_powers import fit_ims_power_laws
from solidification_tool.PDAS_model.pdas import solve_pdas
from solidification_tool.PDAS_visuals.pdas_fits import plot_fits
from solidification_tool.PDAS_visuals.pdas_plot import plot_pdas

from solidification_tool.SDAS_model.sdas import solve_sdas
from solidification_tool.SDAS_visuals.sdas_plot import plot_sdas

from solidification_tool.CET_model.cet import solve_cet
from solidification_tool.CET_visuals.cet_plot import plot_cet

from solidification_tool.io_utils.spacing import normalize_spacing_um

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def get_inputs():
    inputs = SolidificationInputs(
        k_l = 30.5,
        rho_s = 7850,
        c_p = 670,
        L_f = 2.91e5,
        T_f = 1728,
        T_o = 500,

        C_0 = [18.29, 11.55, 1.4],
        C_f = [24.55, 16.30, 3.33],
        k = [1.03, 0.74, 0.75],
        m = [1.92, -6.34, -4.14],
        D = [8e-9, 8e-9, 8e-8],
        Gamma = 2.56e-7,

        NonEq_Freezing_range = 88,

        N0 = 1e12,
        DeltaTN = 2.5
        )
    
    return inputs


def get_heat_transfer(inputs):
    # --------------------------------------------------
    # Solve for heat transfer model: eventually choose
    # --------------------------------------------------
    V, G = solve_steady_state_directional(inputs)

    return(V,G)

def show_heat_transfer(V, G, fig_size):
    # --------------------------------------------------
    # Display heat transfer results
    # --------------------------------------------------
    fig = plot_G_V(V = V, G = G, fig_size = fig_size)
    fig.tight_layout()

    return [fig]

def get_ims (inputs):
    # --------------------------------------------------
    # Solve for IMS model: nice
    # --------------------------------------------------
    ims_results = solve_ims(inputs)

    return(ims_results)

def show_ims(ims_results, Wanted_G, fig_size, plot_range, g_range):
    # --------------------------------------------------
    # Display IMS results
    # --------------------------------------------------
    fig_radius, fig_cool = plot_V_R(ims_results, Wanted_G, fig_size, plot_range= plot_range, G_range= g_range)          # INPUT DESIRED THERMAL GRADIENT G
    return ([fig_radius, fig_cool])

def get_stability_boundaries(ims_results):

    G_out, V_planar, V_dend = extract_stability_boundaries(ims_results)

    return(G_out, V_planar, V_dend)

def show_stability_region(G_out, V_planar, V_dend, fig_size):
    # this needs to go directly in front of PDAS and SDAS!!
    fig, ax = dendritic_stability_edges(G_out, V_planar, V_dend, fig_size)

    return fig, ax

def get_ims_power_laws(ims_results, Wanted_G):

    fit_ims_results = fit_ims_power_laws(ims_results, Wanted_G)

    return(fit_ims_results)

def get_pdas(inputs, V_planar, V_dend, fit_ims_results):
    # --------------------------------------------------
    # Solve for PDAS model
    # --------------------------------------------------
    pdas_results = solve_pdas(inputs, V_min = np.min(V_planar), V_max = np.max(V_dend), fit_ims_results = fit_ims_results)
    
    return(pdas_results)

def show_pdas(pdas_results, G_out, V_planar, V_dend, fig_size):
    fig, ax = show_stability_region(G_out, V_planar, V_dend, fig_size)
    plot_pdas(pdas_results, G_out, V_min_env = V_planar, V_max_env = V_dend, dry_run = False, ax = ax)

    return [fig]

def show_power_law_fits(ims_results, fit_ims_results, Wanted_G, fig_size):
    # show the fits comparatively to V that exist
    fig_fit_radius, fig_fit_cool = plot_fits(ims_results, fit_ims_results, Wanted_G, fig_size)
    return ([fig_fit_radius, fig_fit_cool])

def get_sdas(inputs, V_planar, V_dend, G_out):
    # --------------------------------------------------
    # Solve for SDAS model
    # --------------------------------------------------
    sdas_results = solve_sdas(inputs, V_min = np.min(V_planar), V_max = np.max(V_dend))
    
    return(sdas_results)

def show_sdas(sdas_results, G_out, V_planar, V_dend, fig_size):
    fig, ax = show_stability_region(G_out, V_planar, V_dend, fig_size)
    plot_sdas(sdas_results, G_out, V_min_env = V_planar, V_max_env = V_dend, dry_run = False, ax = ax)

    return [fig]

def show_pdas_sdas(pdas_results, sdas_results, G_out, V_planar, V_dend, fig_size, show_pdas=True, show_sdas=True):

    fig, ax = show_stability_region(G_out, V_planar, V_dend, fig_size)

    # --------------------------------------------------
    # First pass: determine which spacings appear
    # --------------------------------------------------
    shown_pdas = set()
    shown_sdas = set()


    shown_spacings = set()

    if show_pdas:
        shown_pdas = plot_pdas(
            pdas_results,
            G_out,
            V_dend,
            V_planar,
            color_map = None,   # no colors yet
            dry_run = True,      # important
            ax = ax
        )

    if show_sdas:
        shown_sdas = plot_sdas(
            sdas_results,
            G_out,
            V_dend,
            V_planar,
            color_map = None,
            dry_run = True,      # important
            ax = ax
        )

    shown_spacings = shown_pdas | shown_sdas
    
    # --------------------------------------------------
    # Build colormap ONLY from shown spacings
    # --------------------------------------------------
    if not shown_spacings:
        # just return the stability edges plot (no PDAS/SDAS overlays)
        return [fig]
    
    color_map = spacing_to_color(sorted(shown_spacings))
    assert all(isinstance(k, float) for k in color_map.keys())

    # --------------------------------------------------
    # Second pass: actual plotting
    # --------------------------------------------------
    #print(shown_spacings)
    #print(color_map.keys())

    if show_pdas:
        plot_pdas(
            pdas_results,
            G_out,
            V_dend,
            V_planar,
            color_map = color_map,
            dry_run = False,      # important
            ax = ax
        )

    if show_sdas:
        plot_sdas(
            sdas_results,
            G_out,
            V_dend,
            V_planar,
            color_map=color_map,
            dry_run = False,      # important
            ax = ax
        )

    if show_pdas or show_sdas:
        add_pdas_sdas_legend(color_map, shown_spacings)

    ax.set_xlabel("Thermal Gradient G (K/m)")
    ax.set_ylabel("Velocity V (m/s)")
    ax.set_title("PDAS vs SDAS Stability Map")
    ax.grid(True, which="both", ls="--", alpha=0.3)
    fig.tight_layout()

    return [fig]

def get_cet(inputs, fit_ims_results, V_planar, V_dend, G_out):
    # --------------------------------------------------
    # Solve for CET model
    # --------------------------------------------------
    cet_results, phi_list = solve_cet(inputs, fit_ims_results = fit_ims_results, V_min = np.min(V_planar), V_max = np.max(V_dend), G_out = G_out)

    return(cet_results, phi_list)

def show_cet(cet_results, V_planar, V_dend, G_out, fig_size, phi_list):
    fig, ax = show_stability_region(G_out, V_planar, V_dend, fig_size)
    plot_cet(cet_results, phi_list, G_out, V_min_env = V_planar, V_max_env = V_dend, ax = ax)
    fig.tight_layout()
    return [fig]

# COLOR MAP UTILITY

def spacing_to_color(spacings_m):
    """
    Assign consistent colors to spacing values (in meters)
    Returns: {spacing_um (float): color}
    """
    unique = sorted(set(spacings_m))

    cmap = plt.get_cmap("turbo")
    colors = cmap(np.linspace(0.1, 0.9, len(unique)))

    return {lam_um: color for lam_um, color in zip(unique, colors)}


def add_pdas_sdas_legend(color_map, shown_spacings):
    handles = [
        Line2D([0], [0], color="black", lw=2, linestyle="-", label="PDAS"),
        Line2D([0], [0], color="black", lw=2, linestyle="--", label="SDAS"),
    ]

    for s_um in sorted(shown_spacings):
        handles.append(
            Line2D([0], [0], color=color_map[s_um], lw=2,
                   label=f"{int(s_um):.3e} µm")
        )

    plt.legend(
        handles=handles,
        title="Spacing scale & model",
        frameon=False,
        fontsize=9
    )

