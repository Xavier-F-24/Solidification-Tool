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
from solidification_tool.PDAS_model.pdas import solve_pdas
from solidification_tool.SDAS_model.sdas import solve_sdas
from solidification_tool.CET_model.cet import solve_cet
from solidification_tool.core.inputs import SolidificationInputs
from solidification_tool.streamlit_app.config import PRESETS


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

    def test_default_adaptive_output_numerical_fingerprint(self):
        results = self.results

        self.assertEqual(results.V.shape, (100,))
        self.assertEqual(results.ims["G"].shape, (100,))
        self.assertEqual(results.ims["Pe"].shape, (100, 3, 3000))
        self.assertEqual(results.ims["R+"].shape, (100, 3000))
        self.assertEqual(results.ims["V+"].shape, (100, 3, 3000))
        self.assertEqual(results.ims["sampling_mode"], "adaptive")
        self.assertIs(results.ims["R+"], results.ims.R_plus)
        self.assertEqual(set(results.ims.keys()), set(results.ims.to_dict().keys()))
        self.assertEqual(results.ims["P_base"].shape, (100, 3000))
        self.assertEqual(results.ims["Pe_bounds"].shape, (100, 2))
        self.assertEqual(results.ims["Pe_bounds_source"], "refined_discriminant_roots")

        self.assertTrue(np.all(np.diff(results.V) > 0))
        self.assertTrue(np.all(np.diff(results.ims["G"]) > 0))
        self.assertEqual(np.count_nonzero(results.ims["Stable"]), 281907)
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
                7.590857969980113e-08,
                -0.47627337833218103,
                0.9938884735535034,
                33.50255671368625,
                0.266501999396424,
                0.9962642217574339,
            ],
            rtol=1e-12,
        )

    def test_sweep_mode_preserves_global_pe_grid_contract(self):
        results = run_model(get_default_inputs(), settings=EngineSettings(ims_sampling_mode="sweep"))

        self.assertEqual(results.ims.sampling_mode, "sweep")
        self.assertEqual(results.ims.Pe.shape, (3, 3000))
        self.assertEqual(results.ims.P_base.shape, (3000,))
        self.assertIsNone(results.ims.Pe_bounds)
        self.assertIsNone(results.ims.Pe_bounds_source)
        self.assertEqual(np.count_nonzero(results.ims.Stable), 125476)

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

    def test_adaptive_and_sweep_reduced_settings_agree_broadly(self):
        common = dict(
            heat_v_count=12,
            ims_g_count=12,
            ims_pe_count=240,
            spacing_count=4,
            spacing_v_count=15,
            cet_v_count=12,
        )
        sweep = run_model(get_default_inputs(), settings=EngineSettings(**common, ims_sampling_mode="sweep"))
        adaptive = run_model(
            get_default_inputs(),
            settings=EngineSettings(**common, ims_sampling_mode="adaptive"),
        )

        self.assertEqual(len(sweep.stability.G_out), len(adaptive.stability.G_out))
        np.testing.assert_allclose(adaptive.fit_ims.alpha1, sweep.fit_ims.alpha1, rtol=0.05)
        np.testing.assert_allclose(adaptive.fit_ims.beta1, sweep.fit_ims.beta1, rtol=0.05)
        np.testing.assert_allclose(adaptive.fit_ims.alpha2, sweep.fit_ims.alpha2, rtol=0.05)
        np.testing.assert_allclose(adaptive.fit_ims.beta2, sweep.fit_ims.beta2, rtol=0.05)

    def test_adaptive_bounds_contain_sweep_valid_probe_window(self):
        common = dict(
            heat_v_count=12,
            ims_g_count=12,
            ims_pe_count=240,
            spacing_count=4,
            spacing_v_count=15,
            cet_v_count=12,
        )
        sweep = run_model(get_default_inputs(), settings=EngineSettings(**common, ims_sampling_mode="sweep"))
        adaptive = run_model(
            get_default_inputs(),
            settings=EngineSettings(**common, ims_sampling_mode="adaptive"),
        )

        sweep_p = sweep.ims["P_base"]
        sweep_stable = sweep.ims["Stable"]
        adaptive_bounds = adaptive.ims["Pe_bounds"]

        for idx, row_valid in enumerate(sweep_stable):
            if not np.any(row_valid):
                self.assertTrue(np.all(np.isnan(adaptive_bounds[idx])))
                continue

            valid_p = sweep_p[row_valid]
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

    def test_stability_boundaries_are_positive_for_all_presets(self):
        settings = EngineSettings(
            heat_v_count=12,
            ims_g_count=12,
            ims_pe_count=120,
            spacing_count=4,
            spacing_v_count=15,
            cet_v_count=12,
        )

        for preset in PRESETS.values():
            inputs = SolidificationInputs(
                **preset["heat_transfer"],
                **preset["composition"],
                **preset["model_params"],
            )
            results = run_model(inputs, settings=settings)

            self.assertGreater(len(results.stability.G_out), 0)
            self.assertTrue(np.all(np.diff(results.stability.G_out) > 0))
            self.assertTrue(np.all(results.stability.V_planar > 0))
            self.assertTrue(np.all(results.stability.V_dend > 0))

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
            "Pe": np.array([[1.0, 2.0, 3.0, 4.0]]),
            "V+": np.array([[[1.0, 2.0, -3.0, np.nan]]]),
            "V-": np.array([[[1.0, 2.0, -3.0, np.nan]]]),
            "R+": np.array([[1.0, 0.5, 0.25, np.nan]]),
            "R-": np.array([[1.0, 0.5, 0.25, np.nan]]),
            "Total_undercooling": np.array([[1.0, 0.0, 2.0, np.nan]]),
            "Stable": np.array([[True, True, True, False]]),
            "Solute_undercooling": np.array([[1.0, 0.0, 2.0, np.nan]]),
            "Curvature_undercooling": np.array([[1.0, 1.0, 1.0, np.nan]]),
        }

        with self.assertRaisesRegex(EngineComputationError, "finite positive points"):
            fit_ims_power_laws(ims_results, 1.0)

    def test_pdas_rejects_invalid_velocity_domain(self):
        with self.assertRaisesRegex(EngineComputationError, "V_min"):
            solve_pdas(
                get_default_inputs(),
                V_min=1.0,
                V_max=1.0,
                fit_ims_results=self.results.fit_ims,
                settings=EngineSettings(spacing_count=3, spacing_v_count=5),
            )

    def test_sdas_rejects_invalid_log_domain(self):
        inputs = copy.deepcopy(get_default_inputs())
        inputs.C_f = list(inputs.C_0)

        with self.assertRaisesRegex(EngineComputationError, "denominator"):
            solve_sdas(
                inputs,
                V_min=1e-6,
                V_max=1e-3,
                settings=EngineSettings(spacing_count=3, spacing_v_count=5),
            )

    def test_cet_rejects_invalid_fit_domain(self):
        bad_fit = dict(self.results.fit_ims.to_dict())
        bad_fit["beta2"] = -abs(bad_fit["beta2"])

        with self.assertRaisesRegex(EngineComputationError, "fit coefficients"):
            solve_cet(
                get_default_inputs(),
                V_min=1e-6,
                V_max=1e-3,
                fit_ims_results=bad_fit,
                G_out=np.array([1e5]),
                settings=EngineSettings(cet_v_count=5),
            )


if __name__ == "__main__":
    unittest.main()
