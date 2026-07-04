#----------------------------------------
#  CURRENT VERSION: V 1.0
#----------------------------------------
#----------------------------------------
#  CURRENT VERSION: V 1.1
#----------------------------------------

from __future__ import annotations

from matplotlib.figure import Figure

from solidification_tool.io_utils.results_io import save_results, load_results
from solidification_tool.io_utils.run_metadata import RunMetadata
from solidification_tool.io_utils.figure_io import save_figure

from solidification_tool.core.inputs import SolidificationInputs
from solidification_tool.core.results import SimulationResults

from solidification_tool.core.pipeline import (
    get_inputs,
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
    show_cet,
)


def run_simulation(
    inputs: SolidificationInputs | None = None,
    *,
    Wanted_G: float = 1e5,
    run_name: str = "baseline_run",
    notes: str = "Initial full model coupling",
) -> SimulationResults:
    """Run the full coupled pipeline.

    If `inputs` is None, defaults are loaded via `get_inputs()`.
    """

    if inputs is None:
        inputs = get_inputs()

    metadata = RunMetadata.create(run_name=run_name, notes=notes)

    V, G = get_heat_transfer(inputs)
    ims_results = get_ims(inputs)

    G_out, V_planar, V_dend = extract_stability_boundaries(ims_results)

    fit_ims_results = get_ims_power_laws(ims_results, Wanted_G)
    pdas_results = get_pdas(inputs, V_planar, V_dend, fit_ims_results)
    sdas_results = get_sdas(inputs, V_planar, V_dend, G_out)
    cet_results, phi_list = get_cet(inputs, fit_ims_results, V_planar, V_dend, G_out)

    results = SimulationResults(
        inputs=inputs.to_dict(),
        metadata=metadata.__dict__,
        V=V,
        G=G,
        ims=ims_results,
        fit_ims=fit_ims_results,
        stability={"G_out": G_out, "V_planar": V_planar, "V_dend": V_dend},
        pdas=pdas_results,
        sdas=sdas_results,
        cet=cet_results,
        phi_list=phi_list,
    )

    return results


def show_all(
    results: SimulationResults,
    *,
    Wanted_G: float = 1e5,
    show_pdas: bool = True,
    show_sdas: bool = True,
    ims_g_range: list | tuple = (),
) -> dict[str, list[Figure]]:
    """Build all figures as a dict of group -> list[Figure]."""

    fig_size = (8, 6)
    figs: dict[str, list[Figure]] = {}

    figs["heat_transfer"] = show_heat_transfer(results.V, results.G, fig_size)

    if not ims_g_range:
        plot_range = False
        ims_g_range = (1e-9, 1e9)
    else:
        plot_range = True

    figs["ims"] = show_ims(
        results.ims,
        Wanted_G,
        fig_size,
        plot_range=plot_range,
        g_range=ims_g_range,
    )

    figs["ims_fits"] = show_power_law_fits(
        results.ims,
        fit_ims_power_laws(results.ims, Wanted_G),
        Wanted_G,
        fig_size,
    )

    figs["pdas_sdas"] = show_pdas_sdas(
        results.pdas,
        results.sdas,
        results.stability["G_out"],
        results.stability["V_planar"],
        results.stability["V_dend"],
        fig_size,
        show_pdas=show_pdas,
        show_sdas=show_sdas,
    )

    figs["cet"] = show_cet(
        results.cet,
        results.stability["V_planar"],
        results.stability["V_dend"],
        results.stability["G_out"],
        fig_size,
        results.phi_list,
    )

    # Safety: normalize any raw Figure returns into list[Figure]
    for k, v in list(figs.items()):
        if isinstance(v, Figure):
            figs[k] = [v]

    return figs


def save_all_figures(results: SimulationResults, run_dir, *, Wanted_G: float = 1e5):
    fig_dict = show_all(results, Wanted_G=Wanted_G)

    for group, group_figs in fig_dict.items():
        for i, fig in enumerate(group_figs):
            suffix = "" if len(group_figs) == 1 else f"_{i+1}"
            save_figure(fig, run_dir, f"{group}{suffix}")


__all__ = [
    "run_simulation",
    "show_all",
    "save_all_figures",
    "save_results",
    "load_results",
]
