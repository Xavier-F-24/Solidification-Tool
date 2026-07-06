"""
Streamlit-specific cache helpers.

The UI caches the public engine entrypoint instead of orchestrating engine
internals. That keeps Streamlit replaceable without changing the simulation
pipeline itself.
"""

import hashlib
import json
from typing import Any

import streamlit as st

from solidification_tool.app_api import EngineSettings, SolidificationInputs, run_model


def _stable_hash(payload: dict[str, Any]) -> str:
    json_str = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.md5(json_str.encode()).hexdigest()


def hash_inputs(inputs_dict: dict[str, Any]) -> str:
    return _stable_hash(inputs_dict)


def settings_to_payload(settings: EngineSettings) -> dict[str, Any]:
    return {
        "heat_v_min_exp": settings.heat_v_min_exp,
        "heat_v_max_exp": settings.heat_v_max_exp,
        "heat_v_count": settings.heat_v_count,
        "ims_g_min_exp": settings.ims_g_min_exp,
        "ims_g_max_exp": settings.ims_g_max_exp,
        "ims_g_count": settings.ims_g_count,
        "ims_pe_min_exp": settings.ims_pe_min_exp,
        "ims_pe_max_exp": settings.ims_pe_max_exp,
        "ims_pe_count": settings.ims_pe_count,
        "ims_sampling_mode": settings.ims_sampling_mode,
        "spacing_min_exp": settings.spacing_min_exp,
        "spacing_max_exp": settings.spacing_max_exp,
        "spacing_count": settings.spacing_count,
        "spacing_v_count": settings.spacing_v_count,
        "cet_v_count": settings.cet_v_count,
        "cet_phi_values": tuple(settings.cet_phi_values),
    }


def hash_simulation_payload(
    inputs_dict: dict[str, Any],
    wanted_g: float,
    settings_payload: dict[str, Any],
) -> str:
    return _stable_hash(
        {
            "inputs": inputs_dict,
            "wanted_g": wanted_g,
            "settings": settings_payload,
        }
    )


def get_or_run_simulation(
    inputs: SolidificationInputs,
    wanted_g: float,
    settings: EngineSettings | None = None,
):
    inputs_dict = inputs.to_dict()
    settings = settings or EngineSettings()
    settings_payload = settings_to_payload(settings)

    @st.cache_data(show_spinner="Running simulation...")
    def _solve(
        inputs_payload: dict[str, Any],
        wanted_g_value: float,
        engine_settings_payload: dict[str, Any],
        cache_key: str,
    ):
        del cache_key
        return run_model(
            SolidificationInputs(**inputs_payload),
            wanted_g=wanted_g_value,
            run_name="streamlit_run",
            notes="Streamlit app run",
            settings=EngineSettings(**engine_settings_payload),
        )

    return _solve(
        inputs_dict,
        wanted_g,
        settings_payload,
        hash_simulation_payload(inputs_dict, wanted_g, settings_payload),
    )


def reset_cache():
    st.cache_data.clear()
