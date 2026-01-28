from dataclasses import dataclass
import numpy as np

@dataclass
class SimulationResults:
    # --- inputs & metadata ---
    inputs: dict
    metadata: dict

    # --- IMS ---
    V: np.ndarray
    G: np.ndarray
    ims: dict
    fit_ims: dict
    stability: dict

    # --- microstructure ---
    pdas: dict
    sdas: dict
    cet: dict
    phi_list: list