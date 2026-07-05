import math

from solidification_tool.core.inputs import SolidificationInputs
from solidification_tool.core.settings import EngineSettings


class EngineInputError(ValueError):
    pass


def _is_positive_number(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and value > 0


def _as_sequence(value, name: str):
    if isinstance(value, (str, bytes)) or not hasattr(value, "__len__") or not hasattr(value, "__iter__"):
        raise EngineInputError(f"{name} must be a non-empty numeric sequence.")
    if len(value) == 0:
        raise EngineInputError(f"{name} must be non-empty.")
    return value


def validate_inputs(inputs: SolidificationInputs) -> None:
    scalar_positive = [
        "k_l",
        "rho_s",
        "c_p",
        "L_f",
        "T_f",
        "T_o",
        "Gamma",
        "NonEq_Freezing_range",
        "N0",
        "DeltaTN",
    ]

    for name in scalar_positive:
        value = getattr(inputs, name)
        if not _is_positive_number(value):
            raise EngineInputError(f"{name} must be a positive finite number.")

    if inputs.T_f <= inputs.T_o:
        raise EngineInputError("T_f must be greater than T_o.")

    arrays = {
        name: _as_sequence(getattr(inputs, name), name)
        for name in ["C_0", "C_f", "k", "m", "D"]
    }
    lengths = {name: len(value) for name, value in arrays.items()}
    if len(set(lengths.values())) != 1:
        detail = ", ".join(f"{name}={length}" for name, length in lengths.items())
        raise EngineInputError(f"Solute input lengths must match ({detail}).")

    for name, values in arrays.items():
        for idx, value in enumerate(values):
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise EngineInputError(f"{name}[{idx}] must be a finite number.")

    for idx, value in enumerate(arrays["D"]):
        if value <= 0:
            raise EngineInputError(f"D[{idx}] must be positive.")


def validate_settings(settings: EngineSettings) -> None:
    positive_counts = [
        "heat_v_count",
        "ims_g_count",
        "ims_pe_count",
        "spacing_count",
        "spacing_v_count",
        "cet_v_count",
    ]
    for name in positive_counts:
        value = getattr(settings, name)
        if not isinstance(value, int) or value <= 0:
            raise EngineInputError(f"{name} must be a positive integer.")

    ranges = [
        ("heat_v_min_exp", "heat_v_max_exp"),
        ("ims_g_min_exp", "ims_g_max_exp"),
        ("ims_pe_min_exp", "ims_pe_max_exp"),
        ("spacing_min_exp", "spacing_max_exp"),
    ]
    for low_name, high_name in ranges:
        low = getattr(settings, low_name)
        high = getattr(settings, high_name)
        if not (math.isfinite(low) and math.isfinite(high) and low < high):
            raise EngineInputError(f"{low_name} must be less than {high_name}.")

    if len(settings.cet_phi_values) == 0:
        raise EngineInputError("cet_phi_values must be non-empty.")
    for idx, phi in enumerate(settings.cet_phi_values):
        if not isinstance(phi, (int, float)) or not math.isfinite(phi) or not 0 < phi < 1:
            raise EngineInputError(f"cet_phi_values[{idx}] must be between 0 and 1.")
