import json
from pathlib import Path

import numpy as np

from solidification_tool.core.results import ImsPowerLawFit, SimulationResults, StabilityBoundaries


def _plain_mapping(value):
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


def _load_npz_item(data, key):
    value = data[key]
    if getattr(value, "shape", None) == ():
        return value.item()
    return value


def _load_optional_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, "r") as f:
        return json.load(f)


def save_results(results: SimulationResults, run_dir):
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        run_dir / "run.npz",
        inputs=results.inputs,
        metadata=results.metadata,
        V=results.V,
        G=results.G,
        ims=results.ims,
        fit_ims=_plain_mapping(results.fit_ims),
        stability=_plain_mapping(results.stability),
        pdas=results.pdas,
        sdas=results.sdas,
        cet=results.cet,
        phi_list=results.phi_list,
    )

    with open(run_dir / "inputs.json", "w") as f:
        json.dump(results.inputs, f, indent=2)

    with open(run_dir / "metadata.json", "w") as f:
        json.dump(results.metadata, f, indent=2)

    with open(run_dir / "notes.txt", "w") as f:
        f.write(results.metadata.get("notes", ""))


def load_results(filepath):
    filepath = Path(filepath)
    data = np.load(filepath, allow_pickle=True)

    inputs = _load_npz_item(data, "inputs") if "inputs" in data else _load_optional_json(filepath.with_name("inputs.json"), {})
    metadata = (
        _load_npz_item(data, "metadata")
        if "metadata" in data
        else _load_optional_json(filepath.with_name("metadata.json"), {})
    )
    fit_ims = _load_npz_item(data, "fit_ims")
    stability = _load_npz_item(data, "stability")

    if isinstance(fit_ims, dict):
        fit_ims = ImsPowerLawFit(**fit_ims)
    if isinstance(stability, dict):
        stability = StabilityBoundaries(**stability)

    return SimulationResults(
        inputs=inputs,
        metadata=metadata,
        V=data["V"],
        G=data["G"],
        ims=_load_npz_item(data, "ims"),
        fit_ims=fit_ims,
        stability=stability,
        pdas=_load_npz_item(data, "pdas"),
        sdas=_load_npz_item(data, "sdas"),
        cet=_load_npz_item(data, "cet"),
        phi_list=list(_load_npz_item(data, "phi_list")),
    )

