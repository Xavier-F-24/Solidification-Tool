from collections.abc import Mapping
from dataclasses import dataclass, asdict
import numpy as np


@dataclass(frozen=True)
class DictCompatibleDataclass(Mapping):
    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        return iter(asdict(self))

    def __len__(self):
        return len(asdict(self))

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class StabilityBoundaries(DictCompatibleDataclass):
    G_out: np.ndarray
    V_planar: np.ndarray
    V_dend: np.ndarray


@dataclass(frozen=True)
class ImsPowerLawFit(DictCompatibleDataclass):
    alpha1: float
    beta1: float
    R2_radius: float
    alpha2: float
    beta2: float
    R2_undercooling: float


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
