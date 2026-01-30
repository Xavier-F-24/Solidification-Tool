#----------------------------------------
#  CURRENT VERSION: V 0.3
#----------------------------------------

import matplotlib
#matplotlib.use("Agg")

import matplotlib.pyplot as plt

import numpy as np

from io_utils.results_io import save_results, load_results
from io_utils.run_metadata import RunMetadata
from io_utils.run_manager import create_run_folder
from io_utils.figure_io import save_figure


from core.inputs import SolidificationInputs
from core.results import SimulationResults

from core.pipeline import (get_inputs, 
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


def show_all(results, Wanted_G = 1e5):
    fig_size = (8,6)

    show_heat_transfer(
        results.V, 
        results.G,
        fig_size
        )
    
    show_ims(
        results.ims, 
        Wanted_G,
        fig_size
        )
    
    show_power_law_fits(
        results.ims, 
        fit_ims_power_laws(results.ims, Wanted_G),
        Wanted_G,
        fig_size
        )
    
    show_pdas_sdas(
        results.pdas,
        results.sdas,
        results.stability["G_out"],
        results.stability["V_planar"],
        results.stability["V_dend"],
        fig_size
        )

    show_cet(
        results.cet,
        results.stability["V_planar"],
        results.stability["V_dend"],
        results.stability["G_out"],
        fig_size,
        results.phi_list
        )
    
    plt.show()


def save_all_figures(results, run_dir, Wanted_G = 1e5):
    fig_size = (8,6)

    fig = show_heat_transfer(results.V, results.G, fig_size)
    save_figure(fig, run_dir, "heat_transfer")

    fig_radius, fig_cool = show_ims(results.ims, Wanted_G, fig_size)
    save_figure(fig_radius, run_dir, "ims_radius")
    save_figure(fig_cool, run_dir, "ims_cool")

    fig_fit_radius, fig_fit_cool = show_power_law_fits(
        results.ims,
        fit_ims_power_laws(results.ims, Wanted_G),
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



if __name__ == "__main__":
    print("YEHAH")

    #run_dir = create_run_folder("baseline_class_alloy")

    #results = run_simulation()

    #save_results(results, run_dir)

    #show_all(results)

    #save_all_figures(results, run_dir)
    

    results = load_results("C:/Users/xavie/Desktop/solidification_tool\results\2026-01-28_21-24-14_baseline_class_alloy\run.npz")
    show_all(results)



    
