
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

@dataclass
class SimulationResults:
    V: np.ndarray
    G: np.ndarray
    ims: dict
    stability: dict
    pdas: dict
    sdas: dict
    cet: dict


def get_inputs():
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
    
    return inputs

def get_heat_transfer(inputs):
    # --------------------------------------------------
    # Solve for heat transfer model: eventually choose
    # --------------------------------------------------
    V, G = solve_steady_state_directional(inputs)

    return(V,G)

def show_heat_transfer(V, G):
    # --------------------------------------------------
    # Display heat transfer results
    # --------------------------------------------------
    fig = plot_G_V(V, G)

    return(fig)

def get_ims (inputs):
    # --------------------------------------------------
    # Solve for IMS model: nice
    # --------------------------------------------------
    ims_results = solve_ims(inputs)

    return(ims_results)

def show_ims(ims_results, Wanted_G):
    # --------------------------------------------------
    # Display IMS results
    # --------------------------------------------------
    fig = plot_V_R(ims_results, Wanted_G)          # INPUT DESIRED THERMAL GRADIENT G
    return(fig)

def get_stability_boundaries(ims_results):

    G_out, V_planar, V_dend = extract_stability_boundaries(ims_results)

    return(G_out, V_planar, V_dend)

def show_stability_region(G_out, V_planar, V_dend):
    # this needs to go directly in front of PDAS and SDAS!!
    fig = dendritic_stability_edges(G_out, V_planar, V_dend)

    return(fig)

def get_ims_power_laws(ims_results, Wanted_G):

    fit_ims_results = fit_ims_power_laws(ims_results, Wanted_G)

    return(fit_ims_results)

def get_pdas(inputs, V_planar, V_dend, fit_ims_results):
    # --------------------------------------------------
    # Solve for PDAS model
    # --------------------------------------------------
    pdas_results = solve_pdas(inputs, V_min = np.min(V_planar), V_max = np.max(V_dend), fit_ims_results = fit_ims_results)
    
    return(pdas_results)

def show_pdas(pdas_results, G_out, V_planar, V_dend):
    fi = show_stability_region(G_out, V_planar, V_dend)
    fig = plot_pdas(pdas_results, G_out, V_min_env = V_planar, V_max_env = V_dend)

    return(fig)

def show_power_law_fits(ims_results, fit_ims_results, Wanted_G):
    # show the fits comparatively to V that exist
    fig5 = plot_fits(ims_results, fit_ims_results, Wanted_G)
    return(fig5)

def get_sdas(inputs, V_planar, V_dend, G_out):
    # --------------------------------------------------
    # Solve for SDAS model
    # --------------------------------------------------
    sdas_results = solve_sdas(inputs, V_min = np.min(V_planar), V_max = np.max(V_dend))
    
    return(sdas_results)

def show_sdas(sdas_results, G_out, V_planar, V_dend):
    fi = show_stability_region(G_out, V_planar, V_dend)
    fig = plot_sdas(sdas_results, G_out, V_min_env = V_planar, V_max_env = V_dend)

    return(fig)

def show_pdas_sdas(pdas_results, sdas_results, G_out, V_planar, V_dend):
    f = show_stability_region(G_out, V_planar, V_dend)
    fi = plot_pdas(pdas_results, G_out, V_min_env = V_planar, V_max_env = V_dend)
    fig = plot_sdas(sdas_results, G_out, V_min_env = V_planar, V_max_env = V_dend)

    return(fig)

def get_cet(inputs, fit_ims_results, V_planar, V_dend):
    # --------------------------------------------------
    # Solve for CET model
    # --------------------------------------------------
    cet_results = solve_cet(inputs, fit_ims_results = fit_ims_results, V_min = np.min(V_planar), V_max = np.max(V_dend))

    return(cet_results)

def show_cet(cet_results, V_planar, V_dend, G_out):
    fi = show_stability_region(G_out, V_planar, V_dend)
    fig = plot_cet(cet_results)
    return(fig)


def run_all():
    Wanted_G = 1e5

    inputs = get_inputs()
    V,G = get_heat_transfer(inputs)
    ims_results = get_ims(inputs)
    (G_out, V_planar, V_dend) = extract_stability_boundaries(ims_results)
    fit_ims_results = get_ims_power_laws(ims_results, Wanted_G)
    pdas_results = get_pdas(inputs, V_planar, V_dend, fit_ims_results)
    sdas_results = get_sdas(inputs, V_planar, V_dend, G_out)
    cet_results = get_cet(inputs, fit_ims_results, V_planar, V_dend)

    show_heat_transfer(V,G)
    show_ims(ims_results, Wanted_G)
    show_power_law_fits(ims_results, fit_ims_results, Wanted_G)
    show_pdas_sdas(pdas_results, sdas_results, G_out, V_planar, V_dend)
    show_cet(cet_results, V_planar, V_dend, G_out)

    plt.show()


if __name__ == "__main__":
    run_all()
    
