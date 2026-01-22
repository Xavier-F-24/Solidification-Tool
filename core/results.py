from dataclasses import dataclass
import numpy as np

@dataclass
class SimulationResults:
    inputs: dict
    metadata: dict
    V: np.ndarray
    G: np.ndarray
    ims: dict
    stability: dict
    pdas: dict
    sdas: dict
    cet: dict