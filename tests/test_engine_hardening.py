import copy
import tempfile
import unittest

import numpy as np

from solidification_tool.app_api import (
    EngineSettings,
    EngineInputError,
    get_default_inputs,
    load_run,
    run_model,
    save_run,
)
from solidification_tool.core.results import ImsPowerLawFit, SimulationResults, StabilityBoundaries


class EngineValidationTests(unittest.TestCase):
    def test_default_inputs_are_valid(self):
        results = run_model(get_default_inputs())
        self.assertIsInstance(results, SimulationResults)

    def test_numpy_array_solute_inputs_are_valid(self):
        inputs = copy.deepcopy(get_default_inputs())
        inputs.C_0 = np.array(inputs.C_0)
        inputs.C_f = np.array(inputs.C_f)
        inputs.k = np.array(inputs.k)
        inputs.m = np.array(inputs.m)
        inputs.D = np.array(inputs.D)

        results = run_model(inputs)

        self.assertIsInstance(results, SimulationResults)

    def test_mismatched_solute_lengths_fail(self):
        inputs = copy.deepcopy(get_default_inputs())
        inputs.D = inputs.D[:-1]

        with self.assertRaisesRegex(EngineInputError, "Solute input lengths must match"):
            run_model(inputs)

    def test_negative_physical_constant_fails(self):
        inputs = copy.deepcopy(get_default_inputs())
        inputs.k_l = -1

        with self.assertRaisesRegex(EngineInputError, "k_l must be a positive"):
            run_model(inputs)

    def test_zero_diffusivity_fails(self):
        inputs = copy.deepcopy(get_default_inputs())
        inputs.D[0] = 0

        with self.assertRaisesRegex(EngineInputError, "D\\[0\\] must be positive"):
            run_model(inputs)

    def test_invalid_temperature_relation_fails(self):
        inputs = copy.deepcopy(get_default_inputs())
        inputs.T_o = inputs.T_f

        with self.assertRaisesRegex(EngineInputError, "T_f must be greater than T_o"):
            run_model(inputs)


class EngineRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = run_model(get_default_inputs())

    def test_default_engine_output_shape_contract(self):
        results = self.results

        self.assertIsInstance(results, SimulationResults)
        self.assertIsInstance(results.fit_ims, ImsPowerLawFit)
        self.assertIsInstance(results.stability, StabilityBoundaries)

        self.assertGreater(results.V.size, 0)
        self.assertGreater(results.G.size, 0)
        self.assertTrue(np.any(np.isfinite(results.V)))
        self.assertTrue(np.any(np.isfinite(results.G)))

        for key in ["G", "Pe", "R+", "V+", "Total_undercooling", "Stable"]:
            self.assertIn(key, results.ims)

        for key in ["G_out", "V_planar", "V_dend"]:
            self.assertIn(key, results.stability)
            self.assertGreater(results.stability[key].size, 0)

        for key in ["alpha1", "beta1", "R2_radius", "alpha2", "beta2", "R2_undercooling"]:
            self.assertIn(key, results.fit_ims)
            self.assertTrue(np.isfinite(results.fit_ims[key]))

        self.assertGreater(len(results.pdas), 0)
        self.assertGreater(len(results.sdas), 0)
        self.assertGreater(len(results.cet), 0)
        self.assertGreater(len(results.phi_list), 0)

    def test_save_load_round_trip_preserves_result_sections(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_run(self.results, tmp_dir)
            loaded = load_run(f"{tmp_dir}/run.npz")

        self.assertIsInstance(loaded, SimulationResults)
        self.assertIsInstance(loaded.fit_ims, ImsPowerLawFit)
        self.assertIsInstance(loaded.stability, StabilityBoundaries)
        self.assertEqual(self.results.V.shape, loaded.V.shape)
        self.assertEqual(self.results.G.shape, loaded.G.shape)
        self.assertEqual(set(self.results.ims.keys()), set(loaded.ims.keys()))
        self.assertEqual(set(self.results.pdas.keys()), set(loaded.pdas.keys()))
        self.assertEqual(set(self.results.sdas.keys()), set(loaded.sdas.keys()))
        self.assertEqual(set(self.results.cet.keys()), set(loaded.cet.keys()))
        self.assertEqual(self.results.phi_list, loaded.phi_list)

    def test_engine_settings_can_reduce_grid_sizes(self):
        settings = EngineSettings(
            heat_v_count=12,
            ims_g_count=8,
            ims_pe_count=80,
            spacing_count=4,
            spacing_v_count=15,
            cet_v_count=12,
            cet_phi_values=(0.01,),
        )

        results = run_model(get_default_inputs(), settings=settings)

        self.assertEqual(results.V.shape, (12,))
        self.assertEqual(results.ims["G"].shape, (8,))
        self.assertEqual(len(results.pdas), 4)
        self.assertEqual(len(results.sdas), 4)
        self.assertEqual(results.phi_list, [0.01])


if __name__ == "__main__":
    unittest.main()
