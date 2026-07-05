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

from solidification_tool.app_api import SolidificationInputs, run_model


def hash_inputs(inputs_dict: dict[str, Any]) -> str:
    json_str = json.dumps(inputs_dict, sort_keys=True, default=str)
    return hashlib.md5(json_str.encode()).hexdigest()


def get_or_run_simulation(inputs: SolidificationInputs, wanted_g: float):
    inputs_dict = inputs.to_dict()

    @st.cache_data(show_spinner="Running simulation...")
    def _solve(inputs_payload: dict[str, Any], wanted_g_value: float):
        return run_model(
            SolidificationInputs(**inputs_payload),
            wanted_g=wanted_g_value,
            run_name="streamlit_run",
            notes="Streamlit app run",
        )

    return _solve(inputs_dict, wanted_g)


def reset_cache():
    st.cache_data.clear()
