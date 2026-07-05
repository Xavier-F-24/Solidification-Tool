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

from solidification_tool.core.inputs import SolidificationInputs


def hash_inputs(inputs_dict: dict[str, Any]) -> str:
    json_str = json.dumps(inputs_dict, sort_keys=True, default=str)
    return hashlib.md5(json_str.encode()).hexdigest()


def get_or_run_simulation(inputs: SolidificationInputs, wanted_g: float):
    from solidification_tool.core.engine import run_simulation

    inputs_dict = inputs.to_dict()

    @st.cache_data(show_spinner="Running simulation...")
    def _solve(inputs_payload: dict[str, Any], wanted_g_value: float):
        return run_simulation(
            SolidificationInputs(**inputs_payload),
            Wanted_G=wanted_g_value,
            run_name="streamlit_run",
            notes="Streamlit app run",
        )

    return _solve(inputs_dict, wanted_g)


def reset_cache():
    st.cache_data.clear()

