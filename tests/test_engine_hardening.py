import copy
import tempfile
import unittest

import numpy as np

from solidification_tool.app_api import (
    EngineComputationError,
    EngineSettings,
    EngineInputError,
    ImsResults,
    get_default_inputs,
    load_run,
    run_model,
    save_run,
)
from solidification_tool.core.results import ImsPowerLawFit, SimulationResults, StabilityBoundaries
from solidification_tool.PDAS_model.fit_powers import fit_ims_power_laws


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
        self.assertIsInstance(results.ims, ImsResults)
        self.assertIsInstance(results.fit_ims, ImsPowerLawFit)
        self.assertIsInstance(results.stability, StabilityBoundaries)

        self.assertGreater(results.V.size, 0)
        self.assertGreater(results.G.size, 0)
        self.assertTrue(np.any(np.isfinite(results.V)))
        self.assertTrue(np.any(np.isfinite(results.G)))

        for key in ["G", "Pe", "R+", "V+", "Total_undercooling", "Stable"]:
            self.assertIn(key, results.ims)
        for key in ["P_base", "Pe_bounds", "sampling_mode"]:
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

    def test_default_legacy_output_numerical_fingerprint(self):
        results = self.results

        self.assertEqual(results.V.shape, (100,))
        self.assertEqual(results.ims["G"].shape, (100,))
        self.assertEqual(results.ims["Pe"].shape, (3, 3000))
        self.assertEqual(results.ims["R+"].shape, (100, 3000))
        self.assertEqual(results.ims["V+"].shape, (100, 3, 3000))
        self.assertEqual(results.ims["sampling_mode"], "legacy")
        self.assertIs(results.ims["R+"], results.ims.R_plus)
        self.assertEqual(set(results.ims.keys()), set(results.ims.to_dict().keys()))
        self.assertEqual(results.ims["P_base"].shape, (3000,))
        self.assertIsNone(results.ims["Pe_bounds"])
        self.assertIsNone(results.ims["Pe_bounds_source"])

        self.assertTrue(np.all(np.diff(results.V) > 0))
        self.assertTrue(np.all(np.diff(results.ims["G"]) > 0))
        self.assertEqual(np.count_nonzero(results.ims["Stable"]), 125476)
        self.assertEqual(results.stability.G_out.shape, (94,))

        np.testing.assert_allclose([np.nanmin(results.V), np.nanmax(results.V)], [1e-6, 1e6])
        np.testing.assert_allclose(
            [np.nanmin(results.G), np.nanmax(results.G)],
            [136.8628196721311, 136862819672131.12],
        )
        np.testing.assert_allclose(
            [
                results.fit_ims.alpha1,
                results.fit_ims.beta1,
                results.fit_ims.R2_radius,
                results.fit_ims.alpha2,
                results.fit_ims.beta2,
                results.fit_ims.R2_undercooling,
            ],
            [
                7.573924908807277e-08,
                -0.4767301821392265,
                0.9939267709884884,
                33.521622048506046,
                0.2665956848499376,
                0.9962952298438021,
            ],
            rtol=1e-12,
        )

    def test_default_outputs_are_physically_positive_where_finite(self):
        results = self.results

        for key in ["R+", "V+", "Total_undercooling", "Curvature_undercooling"]:
            values = results.ims[key]
            finite = values[np.isfinite(values)]
            self.assertGreater(finite.size, 0)
            self.assertTrue(np.all(finite > 0), key)

        self.assertTrue(np.all(results.stability.G_out > 0))
        self.assertTrue(np.all(results.stability.V_planar > 0))
        self.assertTrue(np.all(results.stability.V_dend > 0))
        self.assertGreater(results.fit_ims.R2_radius, 0.99)
        self.assertGreater(results.fit_ims.R2_undercooling, 0.99)

    def test_save_load_round_trip_preserves_result_sections(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_run(self.results, tmp_dir)
            loaded = load_run(f"{tmp_dir}/run.npz")

        self.assertIsInstance(loaded, SimulationResults)
        self.assertIsInstance(loaded.ims, ImsResults)
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

    def test_adaptive_ims_sampling_preserves_rectangular_contract(self):
        settings = EngineSettings(
            heat_v_count=12,
            ims_g_count=12,
            ims_pe_count=240,
            ims_sampling_mode="adaptive",
            spacing_count=4,
            spacing_v_count=15,
            cet_v_count=12,
            cet_phi_values=(0.01,),
        )

        results = run_model(get_default_inputs(), settings=settings)

        self.assertEqual(results.ims["sampling_mode"], "adaptive")
        self.assertEqual(results.ims["G"].shape, (12,))
        self.assertEqual(results.ims["Pe"].shape, (12, 3, 240))
        self.assertEqual(results.ims["P_base"].shape, (12, 240))
        self.assertEqual(results.ims["Pe_bounds"].shape, (12, 2))
        self.assertEqual(results.ims["Pe_bounds_source"], "refined_discriminant_roots")
        self.assertGreater(np.count_nonzero(results.ims["Stable"]), 0)
        self.assertEqual(results.metadata["engine_settings"]["ims_sampling_mode"], "adaptive")

        finite_bounds = results.ims["Pe_bounds"][np.isfinite(results.ims["Pe_bounds"][:, 0])]
        self.assertGreater(len(finite_bounds), 0)
        self.assertTrue(np.all(finite_bounds[:, 0] <= finite_bounds[:, 1]))
        self.assertGreater(results.fit_ims.R2_radius, 0.99)
        self.assertGreater(results.fit_ims.R2_undercooling, 0.99)

    def test_adaptive_and_legacy_reduced_settings_agree_broadly(self):
        common = dict(
            heat_v_count=12,
            ims_g_count=12,
            ims_pe_count=240,
            spacing_count=4,
            spacing_v_count=15,
            cet_v_count=12,
        )
        legacy = run_model(get_default_inputs(), settings=EngineSettings(**common))
        adaptive = run_model(
            get_default_inputs(),
            settings=EngineSettings(**common, ims_sampling_mode="adaptive"),
        )

        self.assertEqual(len(legacy.stability.G_out), len(adaptive.stability.G_out))
        np.testing.assert_allclose(adaptive.fit_ims.alpha1, legacy.fit_ims.alpha1, rtol=0.05)
        np.testing.assert_allclose(adaptive.fit_ims.beta1, legacy.fit_ims.beta1, rtol=0.05)
        np.testing.assert_allclose(adaptive.fit_ims.alpha2, legacy.fit_ims.alpha2, rtol=0.05)
        np.testing.assert_allclose(adaptive.fit_ims.beta2, legacy.fit_ims.beta2, rtol=0.05)

    def test_adaptive_bounds_contain_legacy_valid_probe_window(self):
        common = dict(
            heat_v_count=12,
            ims_g_count=12,
            ims_pe_count=240,
            spacing_count=4,
            spacing_v_count=15,
            cet_v_count=12,
        )
        legacy = run_model(get_default_inputs(), settings=EngineSettings(**common))
        adaptive = run_model(
            get_default_inputs(),
            settings=EngineSettings(**common, ims_sampling_mode="adaptive"),
        )

        legacy_p = legacy.ims["P_base"]
        legacy_stable = legacy.ims["Stable"]
        adaptive_bounds = adaptive.ims["Pe_bounds"]

        for idx, row_valid in enumerate(legacy_stable):
            if not np.any(row_valid):
                self.assertTrue(np.all(np.isnan(adaptive_bounds[idx])))
                continue

            valid_p = legacy_p[row_valid]
            self.assertLessEqual(adaptive_bounds[idx, 0], valid_p[0])
            self.assertGreaterEqual(adaptive_bounds[idx, 1], valid_p[-1])

    def test_adaptive_fit_converges_with_refined_pe_count(self):
        common = dict(
            heat_v_count=12,
            ims_g_count=12,
            ims_sampling_mode="adaptive",
            spacing_count=4,
            spacing_v_count=15,
            cet_v_count=12,
        )
        coarse = run_model(get_default_inputs(), settings=EngineSettings(**common, ims_pe_count=120))
        fine = run_model(get_default_inputs(), settings=EngineSettings(**common, ims_pe_count=480))

        np.testing.assert_allclose(coarse.fit_ims.alpha1, fine.fit_ims.alpha1, rtol=0.04)
        np.testing.assert_allclose(coarse.fit_ims.beta1, fine.fit_ims.beta1, rtol=0.04)
        np.testing.assert_allclose(coarse.fit_ims.alpha2, fine.fit_ims.alpha2, rtol=0.04)
        np.testing.assert_allclose(coarse.fit_ims.beta2, fine.fit_ims.beta2, rtol=0.04)

    def test_invalid_sampling_mode_fails(self):
        settings = EngineSettings(ims_sampling_mode="dense-ish")

        with self.assertRaisesRegex(EngineInputError, "ims_sampling_mode"):
            run_model(get_default_inputs(), settings=settings)

    def test_adaptive_ims_without_valid_window_fails_clearly(self):
        settings = EngineSettings(
            ims_sampling_mode="adaptive",
            ims_g_min_exp=20,
            ims_g_max_exp=21,
            ims_g_count=3,
            ims_pe_count=20,
            heat_v_count=5,
            spacing_count=3,
            spacing_v_count=5,
            cet_v_count=5,
        )

        with self.assertRaisesRegex(EngineComputationError, "no valid Peclet window"):
            run_model(get_default_inputs(), settings=settings)

    def test_ims_power_law_fit_rejects_nonpositive_log_domain(self):
        ims_results = {
            "G": np.array([1.0]),
            "V+": np.array([[[1.0, 2.0, -3.0, np.nan]]]),
            "R+": np.array([[1.0, 0.5, 0.25, np.nan]]),
            "Total_undercooling": np.array([[1.0, 0.0, 2.0, np.nan]]),
        }

        with self.assertRaisesRegex(EngineComputationError, "finite positive points"):
            fit_ims_power_laws(ims_results, 1.0)


if __name__ == "__main__":
    unittest.main()
