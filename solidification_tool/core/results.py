from collections.abc import Mapping
from dataclasses import dataclass, asdict
from typing import ClassVar
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


@dataclass(frozen=True)
class ImsResults(Mapping):
    G: np.ndarray
    Pe: np.ndarray
    P_base: np.ndarray
    Pe_bounds: np.ndarray | None
    Pe_bounds_source: str | None
    sampling_mode: str
    R_plus: np.ndarray
    R_minus: np.ndarray
    V_plus: np.ndarray
    V_minus: np.ndarray
    Total_undercooling: np.ndarray
    Stable: np.ndarray
    Solute_undercooling: np.ndarray
    Curvature_undercooling: np.ndarray

    _KEY_TO_ATTR: ClassVar[dict[str, str]] = {
        "G": "G",
        "Pe": "Pe",
        "P_base": "P_base",
        "Pe_bounds": "Pe_bounds",
        "Pe_bounds_source": "Pe_bounds_source",
        "sampling_mode": "sampling_mode",
        "R+": "R_plus",
        "R-": "R_minus",
        "V+": "V_plus",
        "V-": "V_minus",
        "Total_undercooling": "Total_undercooling",
        "Stable": "Stable",
        "Solute_undercooling": "Solute_undercooling",
        "Curvature_undercooling": "Curvature_undercooling",
    }
    _ATTR_TO_KEY: ClassVar[dict[str, str]] = {value: key for key, value in _KEY_TO_ATTR.items()}

    def __getitem__(self, key):
        return getattr(self, self._KEY_TO_ATTR[key])

    def __iter__(self):
        return iter(self._KEY_TO_ATTR)

    def __len__(self):
        return len(self._KEY_TO_ATTR)

    def to_dict(self):
        return {key: getattr(self, attr) for key, attr in self._KEY_TO_ATTR.items()}

    @classmethod
    def from_dict(cls, values: Mapping):
        normalized = dict(values)
        if normalized.get("sampling_mode") == "legacy":
            normalized["sampling_mode"] = "sweep"
        normalized.setdefault("sampling_mode", "sweep")
        normalized.setdefault("P_base", np.asarray(normalized["Pe"])[0])
        normalized.setdefault("Pe_bounds", None)
        normalized.setdefault("Pe_bounds_source", None)
        return cls(
            **{
                attr: normalized[key]
                for key, attr in cls._KEY_TO_ATTR.items()
                if key in normalized
            }
        )

    def solute_undercooling_at_g(self, idx: int) -> np.ndarray:
        values = np.asarray(self.Solute_undercooling)
        if values.ndim == 3:
            return values[idx]
        return values


@dataclass
class SimulationResults:
    # --- inputs & metadata ---
    inputs: dict
    metadata: dict

    # --- IMS ---
    V: np.ndarray
    G: np.ndarray
    ims: ImsResults | dict
    fit_ims: dict
    stability: dict

    # --- microstructure ---
    pdas: dict
    sdas: dict
    cet: dict
    phi_list: list
