#----------------------------------------
#  CURRENT VERSION: V 1.0
#----------------------------------------

import matplotlib
#matplotlib.use("Agg")
import matplotlib
from matplotlib.figure import Figure

import matplotlib.pyplot as plt

import numpy as np

from solidification_tool.io_utils.results_io import save_results, load_results
from solidification_tool.io_utils.run_metadata import RunMetadata
from solidification_tool.io_utils.run_manager import create_run_folder
from solidification_tool.io_utils.figure_io import save_figure


from solidification_tool.core.inputs import SolidificationInputs
from solidification_tool.core.results import SimulationResults

from solidification_tool.core.pipeline import (get_inputs, 
                           get_heat_transfer, 
                           get_ims,
                           extract_stability_boundaries,
                           get_ims_power_laws, 
                           get_pdas, 
                           get_sdas, 
                           get_cet, 
                           show_heat_transfer,
                           show_ims,
                           show_power_law_fits,
                           fit_ims_power_laws,
                           show_pdas_sdas, 
                           show_cet
                          )

def run_simulation():
    Wanted_G = 1e5

    inputs = get_inputs()

    metadata = RunMetadata.create(
        run_name="baseline_run",
        notes="Initial full model coupling"
    )

    V, G = get_heat_transfer(inputs)
    ims_results = get_ims(inputs)

    G_out, V_planar, V_dend = extract_stability_boundaries(ims_results)

    fit_ims_results = get_ims_power_laws(ims_results, Wanted_G)
    pdas_results = get_pdas(inputs, V_planar, V_dend, fit_ims_results)
    sdas_results = get_sdas(inputs, V_planar, V_dend, G_out)
    cet_results, phi_list  = get_cet(inputs, fit_ims_results, V_planar, V_dend, G_out)

    results =  SimulationResults(
        inputs = inputs.to_dict(),
        metadata = metadata.__dict__,
        V = V,
        G = G,
        ims = ims_results,
        fit_ims = fit_ims_results,
        stability = {
            "G_out": G_out,
            "V_planar": V_planar,
            "V_dend": V_dend
        },
        pdas = pdas_results,
        sdas = sdas_results,
        cet = cet_results,
        phi_list = phi_list
        )

    return(results)

def show_all(results, Wanted_G=1e5, show_pdas=True, show_sdas=True):
    fig_size = (8, 6)

    figs = {}

    """
    def _dbg(name, x):
    
        print(name, "type:", type(x))
        if isinstance(x, list):
            print("  list lens:", len(x), "item types:", [type(i) for i in x])
        elif isinstance(x, Figure):
            print("  (raw Figure)")
    """

    figs["heat_transfer"] = show_heat_transfer(
        results.V,
        results.G,
        fig_size
    )

    figs["ims"] = show_ims(
        results.ims,
        Wanted_G,
        fig_size
    )

    figs["ims_fits"] = show_power_law_fits(
        results.ims,
        fit_ims_power_laws(results.ims, Wanted_G),
        Wanted_G,
        fig_size
    )

    figs["pdas_sdas"] = show_pdas_sdas(
        results.pdas,
        results.sdas,
        results.stability["G_out"],
        results.stability["V_planar"],
        results.stability["V_dend"],
        fig_size,
        show_pdas=show_pdas,
        show_sdas=show_sdas
    )

    figs["cet"] = show_cet(
        results.cet,
        results.stability["V_planar"],
        results.stability["V_dend"],
        results.stability["G_out"],
        fig_size,
        results.phi_list
    )
  
    return figs

"""
def show_allold(results, Wanted_G = 1e5):
    fig_size = (8,6)

    fig_heat = show_heat_transfer(
        results.V, 
        results.G,
        fig_size
        )
    
    fig_ims_radius, fig_ims_cool = show_ims(
        results.ims, 
        Wanted_G,
        fig_size
        )
    
    fig_power_law_fits_radius, fig_power_law_fits_cooling = show_power_law_fits(
        results.ims, 
        fit_ims_power_laws(results.ims, Wanted_G),
        Wanted_G,
        fig_size
        )
    
    fig_pdas_sdas = show_pdas_sdas(
        results.pdas,
        results.sdas,
        results.stability["G_out"],
        results.stability["V_planar"],
        results.stability["V_dend"],
        fig_size
        )

    fig_cet = show_cet(
        results.cet,
        results.stability["V_planar"],
        results.stability["V_dend"],
        results.stability["G_out"],
        fig_size,
        results.phi_list
        )
    
    return{
        "heat_transfer": fig_heat,
        "ims_radius": fig_ims_radius,
        "ims_cool": fig_ims_cool,
        "ims_fits_radius": fig_power_law_fits_radius,
        "ims_fits_cool": fig_power_law_fits_cooling,
        "pdas_sdas": fig_pdas_sdas,
        "cet": fig_cet
        }
"""
"""
def save_all_figuresold(results, run_dir, Wanted_G = 1e5):
    fig_size = (8,6)

    fig = show_heat_transfer(results.V, results.G, fig_size)
    save_figure(fig, run_dir, "heat_transfer")

    fig_radius, fig_cool = show_ims(results.ims, Wanted_G, fig_size)
    save_figure(fig_radius, run_dir, "ims_radius")
    save_figure(fig_cool, run_dir, "ims_cool")

    fig_fit_radius, fig_fit_cool = show_power_law_fits(
        results.ims,
        results.fit_ims,
        Wanted_G,
        fig_size
    )

    save_figure(fig_fit_radius, run_dir, "ims_fits_radius")
    save_figure(fig_fit_cool, run_dir, "ims_fits_cool")

    fig = show_pdas_sdas(
        results.pdas,
        results.sdas,
        results.stability["G_out"],
        results.stability["V_planar"],
        results.stability["V_dend"],
        fig_size
    )
    save_figure(fig, run_dir, "pdas_sdas")

    fig = show_cet(
        results.cet,
        results.stability["V_planar"],
        results.stability["V_dend"],
        results.stability["G_out"],
        fig_size,
        results.phi_list
    )
    save_figure(fig, run_dir, "cet")
"""

def save_all_figures(results, run_dir, Wanted_G=1e5):
    fig_dict = show_all(results, Wanted_G = Wanted_G)

    for group, figs in fig_dict.items():
        for i, fig in enumerate(figs):
            suffix = "" if len(figs) == 1 else f"_{i+1}"
            save_figure(fig, run_dir, f"{group}{suffix}")


if __name__ == "__main__":
    print("YEHAH")
    #--------------------------------
    # Gui Work
    #--------------------------------
    results = run_simulation()
    figs = show_all(results)
    plt.show()


    #--------------------------------
    # Pre-Gui Work
    #--------------------------------
    #run_dir = create_run_folder("baseline_class_alloy")

    #results = run_simulation()

    #save_results(results, run_dir)

    #show_all(results)

    #save_all_figures(results, run_dir)
    

    #results = load_results("C:/Users/xavie/Desktop/solidification_tool\results\2026-01-28_21-24-14_baseline_class_alloy\run.npz")
    #show_all(results)



    
