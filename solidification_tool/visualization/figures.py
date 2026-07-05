from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from solidification_tool.CET_visuals.cet_plot import plot_cet
from solidification_tool.IMS_visuals.V_R_plots import plot_V_R
from solidification_tool.IMS_visuals.stability_plots import dendritic_stability_edges
from solidification_tool.PDAS_model.fit_powers import fit_ims_power_laws
from solidification_tool.PDAS_visuals.pdas_fits import plot_fits
from solidification_tool.PDAS_visuals.pdas_plot import plot_pdas
from solidification_tool.SDAS_visuals.sdas_plot import plot_sdas
from solidification_tool.core.results import SimulationResults
from solidification_tool.heat_visuals.G_V_plots import plot_G_V
from solidification_tool.io_utils.figure_io import save_figure


def show_heat_transfer(v, g, fig_size):
    fig = plot_G_V(V=v, G=g, fig_size=fig_size)
    fig.tight_layout()
    return [fig]


def show_ims(ims_results, wanted_g, fig_size, plot_range, g_range):
    fig_radius, fig_cool = plot_V_R(
        ims_results,
        wanted_g,
        fig_size,
        plot_range=plot_range,
        G_range=g_range,
    )
    return [fig_radius, fig_cool]


def show_stability_region(g_out, v_planar, v_dend, fig_size):
    return dendritic_stability_edges(g_out, v_planar, v_dend, fig_size)


def show_power_law_fits(ims_results, fit_ims_results, wanted_g, fig_size):
    fig_fit_radius, fig_fit_cool = plot_fits(
        ims_results,
        fit_ims_results,
        wanted_g,
        fig_size,
    )
    return [fig_fit_radius, fig_fit_cool]


def show_pdas_sdas(
    pdas_results,
    sdas_results,
    g_out,
    v_planar,
    v_dend,
    fig_size,
    show_pdas=True,
    show_sdas=True,
):
    fig, ax = show_stability_region(g_out, v_planar, v_dend, fig_size)

    shown_pdas = set()
    shown_sdas = set()

    if show_pdas:
        shown_pdas = plot_pdas(
            pdas_results,
            g_out,
            v_dend,
            v_planar,
            color_map=None,
            dry_run=True,
            ax=ax,
        )

    if show_sdas:
        shown_sdas = plot_sdas(
            sdas_results,
            g_out,
            v_dend,
            v_planar,
            color_map=None,
            dry_run=True,
            ax=ax,
        )

    shown_spacings = shown_pdas | shown_sdas
    if not shown_spacings:
        return [fig]

    color_map = spacing_to_color(sorted(shown_spacings))
    assert all(isinstance(k, float) for k in color_map.keys())

    if show_pdas:
        plot_pdas(
            pdas_results,
            g_out,
            v_dend,
            v_planar,
            color_map=color_map,
            dry_run=False,
            ax=ax,
        )

    if show_sdas:
        plot_sdas(
            sdas_results,
            g_out,
            v_dend,
            v_planar,
            color_map=color_map,
            dry_run=False,
            ax=ax,
        )

    if show_pdas or show_sdas:
        add_pdas_sdas_legend(color_map, shown_spacings)

    ax.set_xlabel("Thermal Gradient G (K/m)")
    ax.set_ylabel("Velocity V (m/s)")
    ax.set_title("PDAS vs SDAS Stability Map")
    ax.grid(True, which="both", ls="--", alpha=0.3)
    fig.tight_layout()

    return [fig]


def show_cet(cet_results, v_planar, v_dend, g_out, fig_size, phi_list):
    fig, ax = show_stability_region(g_out, v_planar, v_dend, fig_size)
    plot_cet(cet_results, phi_list, g_out, V_min_env=v_planar, V_max_env=v_dend, ax=ax)
    fig.tight_layout()
    return [fig]


def show_all(
    results: SimulationResults,
    *,
    Wanted_G: float = 1e5,
    show_pdas: bool = True,
    show_sdas: bool = True,
    ims_g_range: list | tuple = (),
) -> dict[str, list[Figure]]:
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

    for key, value in list(figs.items()):
        if isinstance(value, Figure):
            figs[key] = [value]

    return figs


def save_all_figures(results: SimulationResults, run_dir, *, Wanted_G: float = 1e5):
    fig_dict = show_all(results, Wanted_G=Wanted_G)

    for group, group_figs in fig_dict.items():
        for i, fig in enumerate(group_figs):
            suffix = "" if len(group_figs) == 1 else f"_{i + 1}"
            save_figure(fig, run_dir, f"{group}{suffix}")


def spacing_to_color(spacings_m):
    unique = sorted(set(spacings_m))
    cmap = plt.get_cmap("turbo")
    colors = cmap(np.linspace(0.1, 0.9, len(unique)))
    return {lam_um: color for lam_um, color in zip(unique, colors)}


def add_pdas_sdas_legend(color_map, shown_spacings):
    handles = [
        Line2D([0], [0], color="black", lw=2, linestyle="-", label="PDAS"),
        Line2D([0], [0], color="black", lw=2, linestyle="--", label="SDAS"),
    ]

    for spacing_um in sorted(shown_spacings):
        handles.append(
            Line2D(
                [0],
                [0],
                color=color_map[spacing_um],
                lw=2,
                label=f"{int(spacing_um):.3e} um",
            )
        )

    plt.legend(handles=handles, title="Spacing scale & model", frameon=False, fontsize=9)

