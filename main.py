import matplotlib.pyplot as plt

import numpy as np

from io_utils.results_io import save_results, load_results
from io_utils.run_metadata import RunMetadata
from io_utils.run_manager import create_run_folder

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

def run_simulation(run_name):
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
    cet_results  = get_cet(inputs, fit_ims_results, V_planar, V_dend)

    results =  SimulationResults(
        inputs = inputs.to_dict(),
        metadata = metadata.__dict__,
        V = V,
        G = G,
        ims = ims_results,
        stability = {
            "G_out": G_out,
            "V_planar": V_planar,
            "V_dend": V_dend
        },
        pdas = pdas_results,
        sdas = sdas_results,
        cet = cet_results
        )
    
    run_dir = create_run_folder(run_name)
    save_results(results, run_dir)

    return(results)


def show_all(results, Wanted_G = 1e5):

    show_heat_transfer(
        results.V, 
        results.G
        )
    
    show_ims(
        results.ims, 
        Wanted_G
        )
    
    show_power_law_fits(
        results.ims, 
        fit_ims_power_laws(results.ims, Wanted_G),
        Wanted_G
        )
    
    show_pdas_sdas(
        results.pdas,
        results.sdas,
        results.stability["G_out"],
        results.stability["V_planar"],
        results.stability["V_dend"]
        )

    show_cet(
        results.cet,
        results.stability["V_planar"],
        results.stability["V_dend"],
        results.stability["G_out"]
        )

    plt.show()

if __name__ == "__main__":
    print("YEHAH")

    results = run_simulation("baseline_class_alloy")
    show_all(results)

    #results = load_results("results/baseline_class_alloy.npz")
    #show_all(results)



    
