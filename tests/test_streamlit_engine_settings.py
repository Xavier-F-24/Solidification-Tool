import pathlib
import unittest

from solidification_tool.app_api import EngineSettings, PlotSettings, build_figures, get_default_inputs, run_model
from solidification_tool.streamlit_app.caching import hash_simulation_payload, settings_to_payload
from solidification_tool.streamlit_app.inputs_ui import create_engine_settings_from_state


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


class StreamlitEngineSettingsTests(unittest.TestCase):
    def test_default_state_builds_default_engine_settings(self):
        settings = create_engine_settings_from_state({})

        self.assertEqual(settings, EngineSettings())
        self.assertEqual(settings.ims_sampling_mode, "adaptive")

    def test_legacy_state_normalizes_to_sweep(self):
        settings = create_engine_settings_from_state({"ims_sampling_mode": "legacy"})

        self.assertEqual(settings.ims_sampling_mode, "sweep")

    def test_adaptive_state_builds_adaptive_engine_settings(self):
        settings = create_engine_settings_from_state(
            {
                "ims_sampling_mode": "adaptive",
                "ims_g_count": 12,
                "ims_pe_count": 240,
                "spacing_count": 4,
                "spacing_v_count": 15,
                "cet_v_count": 12,
            }
        )

        self.assertEqual(settings.ims_sampling_mode, "adaptive")
        self.assertEqual(settings.ims_g_count, 12)
        self.assertEqual(settings.ims_pe_count, 240)
        self.assertEqual(settings.spacing_count, 4)
        self.assertEqual(settings.spacing_v_count, 15)
        self.assertEqual(settings.cet_v_count, 12)

    def test_engine_exponent_widget_defaults_are_float_cast(self):
        source = (REPO_ROOT / "solidification_tool" / "streamlit_app" / "inputs_ui.py").read_text(
            encoding="utf-8"
        )

        for key in ["ims_g_min_exp", "ims_g_max_exp", "ims_pe_min_exp", "ims_pe_max_exp"]:
            self.assertIn(f'value=float(st.session_state.get("{key}"', source)

    def test_cache_payload_changes_when_engine_settings_change(self):
        inputs_payload = get_default_inputs().to_dict()
        sweep = settings_to_payload(EngineSettings(ims_sampling_mode="sweep"))
        adaptive = settings_to_payload(EngineSettings(ims_sampling_mode="adaptive"))

        self.assertNotEqual(
            hash_simulation_payload(inputs_payload, 1e5, sweep),
            hash_simulation_payload(inputs_payload, 1e5, adaptive),
        )

    def test_streamlit_caching_passes_settings_to_run_model(self):
        caching_source = (REPO_ROOT / "solidification_tool" / "streamlit_app" / "caching.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("settings=EngineSettings(**engine_settings_payload)", caching_source)

    def test_adaptive_streamlit_settings_smoke(self):
        settings = create_engine_settings_from_state(
            {
                "heat_v_count": 12,
                "ims_g_count": 12,
                "ims_pe_count": 120,
                "ims_sampling_mode": "adaptive",
                "spacing_count": 4,
                "spacing_v_count": 15,
                "cet_v_count": 12,
                "cet_phi_values": (0.01,),
            }
        )

        results = run_model(get_default_inputs(), settings=settings)

        self.assertEqual(results.ims["sampling_mode"], "adaptive")
        self.assertEqual(results.metadata["engine_settings"]["ims_sampling_mode"], "adaptive")
        self.assertGreater(results.ims["Stable"].sum(), 0)

    def test_adaptive_streamlit_settings_build_figures(self):
        settings = create_engine_settings_from_state(
            {
                "heat_v_count": 12,
                "ims_g_count": 12,
                "ims_pe_count": 120,
                "ims_sampling_mode": "adaptive",
                "spacing_count": 4,
                "spacing_v_count": 15,
                "cet_v_count": 12,
                "cet_phi_values": (0.01,),
            }
        )
        results = run_model(get_default_inputs(), settings=settings)

        figures = build_figures(results, PlotSettings(wanted_g=1e5))

        self.assertIn("ims", figures)
        self.assertEqual(len(figures["ims"]), 2)


if __name__ == "__main__":
    unittest.main()
