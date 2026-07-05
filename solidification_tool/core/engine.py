from __future__ import annotations

import numpy as np

from solidification_tool.CET_model.cet import solve_cet
from solidification_tool.IMS_model.extract_stability import extract_stability_boundaries
from solidification_tool.IMS_model.ims import solve_ims
from solidification_tool.PDAS_model.fit_powers import fit_ims_power_laws
from solidification_tool.PDAS_model.pdas import solve_pdas
from solidification_tool.SDAS_model.sdas import solve_sdas
from solidification_tool.core.defaults import get_inputs
from solidification_tool.core.inputs import SolidificationInputs
from solidification_tool.core.results import SimulationResults
from solidification_tool.heat_models.steady_state_directional import solve_steady_state_directional
from solidification_tool.io_utils.run_metadata import RunMetadata


def get_heat_transfer(inputs: SolidificationInputs):
    return solve_steady_state_directional(inputs)


def get_ims(inputs: SolidificationInputs):
    return solve_ims(inputs)


def get_stability_boundaries(ims_results):
    return extract_stability_boundaries(ims_results)


def get_ims_power_laws(ims_results, wanted_g: float):
    return fit_ims_power_laws(ims_results, wanted_g)


def get_pdas(inputs: SolidificationInputs, v_planar, v_dend, fit_ims_results):
    return solve_pdas(
        inputs,
        V_min=np.min(v_planar),
        V_max=np.max(v_dend),
        fit_ims_results=fit_ims_results,
    )


def get_sdas(inputs: SolidificationInputs, v_planar, v_dend, _g_out=None):
    return solve_sdas(inputs, V_min=np.min(v_planar), V_max=np.max(v_dend))


def get_cet(inputs: SolidificationInputs, fit_ims_results, v_planar, v_dend, g_out):
    return solve_cet(
        inputs,
        fit_ims_results=fit_ims_results,
        V_min=np.min(v_planar),
        V_max=np.max(v_dend),
        G_out=g_out,
    )


def run_simulation(
    inputs: SolidificationInputs | None = None,
    *,
    Wanted_G: float = 1e5,
    run_name: str = "baseline_run",
    notes: str = "Initial full model coupling",
) -> SimulationResults:
    if inputs is None:
        inputs = get_inputs()

    metadata = RunMetadata.create(run_name=run_name, notes=notes)

    v, g = get_heat_transfer(inputs)
    ims_results = get_ims(inputs)
    g_out, v_planar, v_dend = get_stability_boundaries(ims_results)
    fit_ims_results = get_ims_power_laws(ims_results, Wanted_G)
    pdas_results = get_pdas(inputs, v_planar, v_dend, fit_ims_results)
    sdas_results = get_sdas(inputs, v_planar, v_dend)
    cet_results, phi_list = get_cet(inputs, fit_ims_results, v_planar, v_dend, g_out)

    return SimulationResults(
        inputs=inputs.to_dict(),
        metadata=metadata.__dict__,
        V=v,
        G=g,
        ims=ims_results,
        fit_ims=fit_ims_results,
        stability={"G_out": g_out, "V_planar": v_planar, "V_dend": v_dend},
        pdas=pdas_results,
        sdas=sdas_results,
        cet=cet_results,
        phi_list=phi_list,
    )
