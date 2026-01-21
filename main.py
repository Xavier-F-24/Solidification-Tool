
from heat_models.steady_state_directional import solve_steady_state_directional
from heat_visuals.G_V_plots import plot_G_V

from IMS_model.ims import solve_ims
from IMS_model.extract_stability import extract_stability_boundaries
from IMS_visuals.V_R_plots import plot_V_R
from IMS_visuals.stability_plots import dendritic_stability_edges

from PDAS_model.fit_powers import fit_ims_power_laws
from PDAS_model.pdas import solve_pdas
from PDAS_visuals.pdas_fits import plot_fits
from PDAS_visuals.pdas_plot import plot_pdas

from SDAS_model.sdas import solve_sdas
from SDAS_visuals.sdas_plot import plot_sdas

from CET_model.cet import solve_cet
from CET_visuals.cet_plot import plot_cet

from dataclasses import dataclass

import matplotlib.pyplot as plt

import numpy as np

@dataclass
class SolidificationInputs:
    # --------------------------------------------------
    # Heat transfer model inputs
    # --------------------------------------------------
    k_l: float       # thermal conductivity of liquid [W/m-K]
    rho_s: float     # density of solid [kg/m^3]
    c_p: float       # heat capacity of solid [J/kg-K]
    L_f: float       # latent heat of fusion [J/kg]
    T_f: float       # fusion or furnace temperature [K]
    T_o: float       # outside temperature [K]

    # --------------------------------------------------
    # IMS model inputs
    # --------------------------------------------------
    C_0 : list       # solute concentrations in alloy [wt%]
    C_f : list       # solute concentrations in alloy end solid [wt%]
    k : list         # partition coefficient (local) [-]
    m : list         # liquidus slopes (local) [K / wt%]
    D : list         # diffusivity [something, Xavier forgets]
    Gamma : float    # given value [-]

    # --------------------------------------------------
    # PDAS inputs
    # --------------------------------------------------
    NonEq_Freezing_range : float # given value of to eutectic (usually) [K]
    
    # --------------------------------------------------
    # CET inputs
    # --------------------------------------------------
    N0 : float # innoculant particles concentration [1/m^3]
    DeltaTN : float # the temperature decrease from a particle (?) [K]

def run_solver():
    inputs = SolidificationInputs(
        k_l=30.5,
        rho_s=7850,
        c_p=670,
        L_f=2.91e5,
        T_f=1728,
        T_o=500,

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

    # --------------------------------------------------
    # Solve for heat transfer model: eventually choose
    # --------------------------------------------------
    V, G = solve_steady_state_directional(inputs)

    # --------------------------------------------------
    # Display heat transfer results
    # --------------------------------------------------
    fig1 = plot_G_V(V, G)

    # --------------------------------------------------
    # Solve for IMS model: nice
    # --------------------------------------------------
    ims_results = solve_ims(inputs)

    # --------------------------------------------------
    # Display IMS results
    # --------------------------------------------------
    fig2 = plot_V_R(ims_results, 1e5)          # INPUT DESIRED THERMAL GRADIENT G
    G_out, V_planar, V_dend = extract_stability_boundaries(ims_results)
    # this needs to go directly in front of PDAS and SDAS!!
    fig3 = dendritic_stability_edges(G_out, V_planar, V_dend)

    # --------------------------------------------------
    # Solve for PDAS model
    # --------------------------------------------------
    fit_ims_results = fit_ims_power_laws(ims_results, 1e5)
    pdas_results = solve_pdas(inputs, V_min = np.min(V_planar), V_max = np.max(V_dend), fit_ims_results = fit_ims_results)
    fig4 = plot_pdas(pdas_results, G_out, V_min_env = V_planar, V_max_env = V_dend)
    # show the fits comparatively to V that exist
    fig5 = plot_fits(ims_results, fit_ims_results, 1e5)

    # --------------------------------------------------
    # Solve for SDAS model
    # --------------------------------------------------
    sdas_results = solve_sdas(inputs, V_min = np.min(V_planar), V_max = np.max(V_dend))
    fig6 = dendritic_stability_edges(G_out, V_planar, V_dend)
    fig7 = plot_sdas(sdas_results, G_out, V_min_env = V_planar, V_max_env = V_dend)

    fig8 = dendritic_stability_edges(G_out, V_planar, V_dend)
    fig9 = plot_pdas(pdas_results, G_out, V_min_env = V_planar, V_max_env = V_dend)
    fig10 = plot_sdas(sdas_results, G_out, V_min_env = V_planar, V_max_env = V_dend)

    # --------------------------------------------------
    # Solve for CET model
    # --------------------------------------------------
    cet_curves = solve_cet(inputs, fit_ims_results = fit_ims_results, V_min = np.min(V_planar), V_max = np.max(V_dend))

    fig11 = dendritic_stability_edges(G_out, V_planar, V_dend)
    fig12 = plot_cet(cet_curves)

    plt.show()



if __name__ == "__main__":
    run_solver()
    # run_instantaneous_point_heat_source()
    # run_instantaneous_moving_point_heat_source()
    # run_semi_infinite_slab_casting
