from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from solidification_tool.core.inputs import SolidificationInputs
from solidification_tool.core.results import ImsResults
from solidification_tool.core.settings import EngineSettings
from solidification_tool.core.validation import EngineComputationError, EngineInputError

if TYPE_CHECKING:
    from solidification_tool.core.results import SimulationResults


@dataclass(frozen=True)
class PlotSettings:
    wanted_g: float = 1e5
    show_pdas: bool = True
    show_sdas: bool = True
    ims_g_range: tuple[float, float] | tuple[()] = ()


def get_default_inputs() -> SolidificationInputs:
    from solidification_tool.core.defaults import get_inputs

    return get_inputs()


def run_model(
    inputs: SolidificationInputs | None = None,
    *,
    wanted_g: float = 1e5,
    run_name: str = "baseline_run",
    notes: str = "Initial full model coupling",
    settings: EngineSettings | None = None,
) -> SimulationResults:
    from solidification_tool.core.engine import run_simulation

    return run_simulation(inputs, Wanted_G=wanted_g, run_name=run_name, notes=notes, settings=settings)


def build_figures(
    results: SimulationResults,
    settings: PlotSettings | None = None,
) -> dict[str, list[Any]]:
    from solidification_tool.visualization.figures import show_all

    settings = settings or PlotSettings()
    return show_all(
        results,
        Wanted_G=settings.wanted_g,
        show_pdas=settings.show_pdas,
        show_sdas=settings.show_sdas,
        ims_g_range=settings.ims_g_range,
    )


def save_run(results: SimulationResults, output_dir: str | Path):
    from solidification_tool.io_utils.results_io import save_results

    return save_results(results, output_dir)


def load_run(path: str | Path) -> SimulationResults:
    from solidification_tool.io_utils.results_io import load_results

    return load_results(path)
