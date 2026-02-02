import numpy as np
from pathlib import Path
import json
from datetime import datetime

def save_results(results, run_dir):
    # Save arrays

    np.savez_compressed(run_dir / "run.npz",
                        V = results.V,
                        G = results.G,
                        ims = results.ims,
                        fit_ims = results.fit_ims,
                        stability = results.stability,
                        pdas = results.pdas,
                        sdas = results.sdas,
                        cet = results.cet,
                        phi_list = results.phi_list)

    # Save inputs + metadata as JSON
    with open(run_dir / "inputs.json", "w") as f:
        json.dump(results.inputs, f, indent=2)

    with open(run_dir / "metadata.json", "w") as f:
        json.dump(results.metadata, f, indent=2)

    # Human-readable notes
    with open(run_dir / "notes.txt", "w") as f:
        f.write(results.metadata.get("notes", ""))

    print(f"Results saved to: {run_dir}")

def load_results(filepath):
    """
    Load SimulationResults from a .npz file.
    """
    data = np.load(filepath, allow_pickle = True)

    from main import SimulationResults  # local import avoids circular issues

    return SimulationResults(
        inputs = data["inputs"],
        metadata = data["metadata"],
        V = data["V"],
        G = data["G"],
        ims = data["ims"].item(), # GPT help - dicts are stored as 0 dimensional arrays - wild
        fit_ims = data["fit_ims"].item(), 
        stability = data["stability"].item(),
        pdas = data["pdas"].item(),
        sdas = data["sdas"].item(),
        cet = data["cet"].item(),
        phi_list = data["phi_list"]
    )

"""
def replay(filepath):
    results = load_results(filepath)
    show_all(results)


def _get_unique_run_dir(base_dir: Path) -> Path:
    
    If base_dir exists, append _001, _002, ... until unique.
    
    if not base_dir.exists():
        return base_dir

    i = 1
    while True:
        candidate = base_dir.with_name(f"{base_dir.name}_{i:03d}")
        if not candidate.exists():
            return candidate
        i += 1
        
"""