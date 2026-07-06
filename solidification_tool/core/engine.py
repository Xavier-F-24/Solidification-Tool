from __future__ import annotations

from dataclasses import asdict

import numpy as np

from solidification_tool.CET_model.cet import solve_cet
from solidification_tool.IMS_model.extract_stability import extract_stability_boundaries
from solidification_tool.IMS_model.ims import solve_ims
from solidification_tool.PDAS_model.fit_powers import fit_ims_power_laws
from solidification_tool.PDAS_model.pdas import solve_pdas
from solidification_tool.SDAS_model.sdas import solve_sdas
from solidification_tool.core.defaults import get_inputs
from solidification_tool.core.inputs import SolidificationInputs
from solidification_tool.core.results import SimulationResults, StabilityBoundaries
from solidification_tool.core.settings import EngineSettings
from solidification_tool.core.validation import validate_inputs, validate_settings
from solidification_tool.heat_models.steady_state_directional import solve_steady_state_directional
from solidification_tool.io_utils.run_metadata import RunMetadata


def get_heat_transfer(inputs: SolidificationInputs, settings: EngineSettings | None = None):
    return solve_steady_state_directional(inputs, settings=settings)


def get_ims(inputs: SolidificationInputs, settings: EngineSettings | None = None):
    return solve_ims(inputs, settings=settings)


def get_stability_boundaries(ims_results):
    g_out, v_planar, v_dend = extract_stability_boundaries(ims_results)
    return StabilityBoundaries(G_out=g_out, V_planar=v_planar, V_dend=v_dend)


def get_ims_power_laws(ims_results, wanted_g: float):
    return fit_ims_power_laws(ims_results, wanted_g)


def get_pdas(inputs: SolidificationInputs, v_planar, v_dend, fit_ims_results, settings: EngineSettings | None = None):
    return solve_pdas(
        inputs,
        V_min=np.min(v_planar),
        V_max=np.max(v_dend),
        fit_ims_results=fit_ims_results,
        settings=settings,
    )


def get_sdas(inputs: SolidificationInputs, v_planar, v_dend, settings: EngineSettings | None = None):
    return solve_sdas(inputs, V_min=np.min(v_planar), V_max=np.max(v_dend), settings=settings)


def get_cet(inputs: SolidificationInputs, fit_ims_results, v_planar, v_dend, g_out, settings: EngineSettings | None = None):
    return solve_cet(
        inputs,
        fit_ims_results=fit_ims_results,
        V_min=np.min(v_planar),
        V_max=np.max(v_dend),
        G_out=g_out,
        settings=settings,
    )


def run_simulation(
    inputs: SolidificationInputs | None = None,
    *,
    Wanted_G: float = 1e5,
    run_name: str = "baseline_run",
    notes: str = "Initial full model coupling",
    settings: EngineSettings | None = None,
) -> SimulationResults:
    if inputs is None:
        inputs = get_inputs()
    settings = settings or EngineSettings()
    validate_inputs(inputs)
    validate_settings(settings)

    metadata = RunMetadata.create(run_name=run_name, notes=notes)
    metadata_dict = metadata.__dict__
    metadata_dict["engine_settings"] = asdict(settings)

    v, g = get_heat_transfer(inputs, settings=settings)
    ims_results = get_ims(inputs, settings=settings)
    stability = get_stability_boundaries(ims_results)
    fit_ims_results = get_ims_power_laws(ims_results, Wanted_G)
    pdas_results = get_pdas(inputs, stability.V_planar, stability.V_dend, fit_ims_results, settings=settings)
    sdas_results = get_sdas(inputs, stability.V_planar, stability.V_dend, settings=settings)
    cet_results, phi_list = get_cet(
        inputs,
        fit_ims_results,
        stability.V_planar,
        stability.V_dend,
        stability.G_out,
        settings=settings,
    )

    return SimulationResults(
        inputs=inputs.to_dict(),
        metadata=metadata_dict,
        V=v,
        G=g,
        ims=ims_results,
        fit_ims=fit_ims_results,
        stability=stability,
        pdas=pdas_results,
        sdas=sdas_results,
        cet=cet_results,
        phi_list=phi_list,
    )
