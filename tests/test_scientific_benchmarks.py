import ast
import pathlib
import unittest

import numpy as np

from solidification_tool.app_api import EngineSettings, get_default_inputs, run_model
from solidification_tool.core.inputs import SolidificationInputs
from solidification_tool.core.model_manifest import MODEL_MANIFEST, MODEL_MANIFEST_VERSION
from solidification_tool.streamlit_app.config import PRESETS


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "solidification_tool"


def _benchmark_settings(**overrides):
    values = dict(
        heat_v_count=16,
        ims_g_count=16,
        ims_pe_count=180,
        spacing_count=4,
        spacing_v_count=16,
        cet_v_count=16,
        cet_phi_values=(0.01, 0.5),
    )
    values.update(overrides)
    return EngineSettings(**values)


def _inputs_from_preset(preset):
    return SolidificationInputs(
        **preset["heat_transfer"],
        **preset["composition"],
        **preset["model_params"],
    )


def _finite_positive(values):
    values = np.asarray(values)
    finite = values[np.isfinite(values)]
    return finite.size > 0 and np.all(finite > 0)


class ScientificManifestTests(unittest.TestCase):
    def test_manifest_covers_all_engine_submodels(self):
        expected = {
            "heat_transfer",
            "ivantsov",
            "ims",
            "stability_boundaries",
            "pdas",
            "sdas",
            "cet",
        }

        self.assertEqual(expected, set(MODEL_MANIFEST))
        self.assertRegex(MODEL_MANIFEST_VERSION, r"^\d{4}\.\d{2}-")

        required_fields = {
            "intent",
            "equations",
            "inputs",
            "outputs",
            "validity",
            "provenance",
            "limitations",
        }
        for name, entry in MODEL_MANIFEST.items():
            self.assertTrue(required_fields.issubset(entry), name)
            self.assertGreater(len(entry["equations"]), 0, name)
            self.assertGreater(len(entry["inputs"]), 0, name)
            self.assertGreater(len(entry["outputs"]), 0, name)
            self.assertIn("[", " ".join(entry["inputs"].values()), name)
            self.assertNotIn("TBD", str(entry), name)

    def test_run_metadata_records_model_manifest_version(self):
        results = run_model(get_default_inputs(), settings=_benchmark_settings())

        manifest = results.metadata["model_manifest"]

        self.assertEqual(manifest["version"], MODEL_MANIFEST_VERSION)
        self.assertEqual(set(manifest["models"]), set(MODEL_MANIFEST))


class ScientificBenchmarkTests(unittest.TestCase):
    def test_all_presets_have_finite_positive_scientific_outputs(self):
        settings = _benchmark_settings()

        for name, preset in PRESETS.items():
            with self.subTest(preset=name):
                results = run_model(_inputs_from_preset(preset), settings=settings)

                self.assertEqual(results.ims.sampling_mode, "adaptive")
                self.assertTrue(np.all(np.diff(results.V) > 0))
                self.assertTrue(np.all(np.diff(results.ims.G) > 0))
                self.assertGreater(len(results.stability.G_out), 0)
                self.assertTrue(np.all(np.diff(results.stability.G_out) > 0))
                self.assertTrue(np.all(results.stability.V_planar > 0))
                self.assertTrue(np.all(results.stability.V_dend > 0))
                self.assertTrue(np.all(results.stability.V_dend >= results.stability.V_planar))
                self.assertGreater(results.fit_ims.R2_radius, 0.95)
                self.assertGreater(results.fit_ims.R2_undercooling, 0.95)
                self.assertTrue(_finite_positive(results.ims.R_plus))
                self.assertTrue(_finite_positive(results.ims.V_plus))
                self.assertTrue(_finite_positive(results.ims.Total_undercooling))

                for curves in [results.pdas, results.sdas]:
                    self.assertGreater(len(curves), 0)
                    for curve in curves.values():
                        self.assertTrue(_finite_positive(curve["V"]))
                        self.assertTrue(_finite_positive(curve["G"]))

                self.assertGreater(len(results.cet), 0)
                for curve in results.cet.values():
                    self.assertTrue(_finite_positive(curve["V"]))
                    g_values = np.asarray(curve["G"])
                    self.assertTrue(np.all(np.isfinite(g_values)))
                    self.assertGreater(np.count_nonzero(g_values > 0), 0)

    def test_adaptive_ims_converges_with_mesh_refinement(self):
        common = dict(
            heat_v_count=16,
            ims_g_count=16,
            spacing_count=4,
            spacing_v_count=16,
            cet_v_count=16,
        )
        coarse = run_model(get_default_inputs(), settings=EngineSettings(**common, ims_pe_count=120))
        medium = run_model(get_default_inputs(), settings=EngineSettings(**common, ims_pe_count=240))
        fine = run_model(get_default_inputs(), settings=EngineSettings(**common, ims_pe_count=480))

        for left, right in [(coarse, medium), (medium, fine)]:
            np.testing.assert_allclose(left.fit_ims.alpha1, right.fit_ims.alpha1, rtol=0.05)
            np.testing.assert_allclose(left.fit_ims.beta1, right.fit_ims.beta1, rtol=0.04)
            np.testing.assert_allclose(left.fit_ims.alpha2, right.fit_ims.alpha2, rtol=0.05)
            np.testing.assert_allclose(left.fit_ims.beta2, right.fit_ims.beta2, rtol=0.04)
            np.testing.assert_allclose(
                np.nanmedian(left.stability.V_planar),
                np.nanmedian(right.stability.V_planar),
                rtol=0.35,
            )
            np.testing.assert_allclose(
                np.nanmedian(left.stability.V_dend),
                np.nanmedian(right.stability.V_dend),
                rtol=0.35,
            )

    def test_adaptive_and_sweep_remain_broadly_comparable(self):
        common = dict(
            heat_v_count=16,
            ims_g_count=16,
            ims_pe_count=240,
            spacing_count=4,
            spacing_v_count=16,
            cet_v_count=16,
        )
        adaptive = run_model(get_default_inputs(), settings=EngineSettings(**common, ims_sampling_mode="adaptive"))
        sweep = run_model(get_default_inputs(), settings=EngineSettings(**common, ims_sampling_mode="sweep"))

        self.assertEqual(adaptive.ims.sampling_mode, "adaptive")
        self.assertEqual(sweep.ims.sampling_mode, "sweep")
        np.testing.assert_allclose(adaptive.fit_ims.alpha1, sweep.fit_ims.alpha1, rtol=0.08)
        np.testing.assert_allclose(adaptive.fit_ims.beta1, sweep.fit_ims.beta1, rtol=0.08)
        np.testing.assert_allclose(adaptive.fit_ims.alpha2, sweep.fit_ims.alpha2, rtol=0.08)
        np.testing.assert_allclose(adaptive.fit_ims.beta2, sweep.fit_ims.beta2, rtol=0.08)
        self.assertGreater(len(adaptive.stability.G_out), 0)
        self.assertGreater(len(sweep.stability.G_out), 0)


class ScientificCleanupTests(unittest.TestCase):
    def test_deprecated_storage_module_is_not_imported_by_active_package(self):
        violations = []
        for path in PACKAGE_ROOT.rglob("*.py"):
            if path.name == "storage.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports = [node.module]
                else:
                    continue

                for imported in imports:
                    if imported == "solidification_tool.storage" or imported.startswith(
                        "solidification_tool.storage."
                    ):
                        violations.append(f"{path.relative_to(REPO_ROOT)} imports {imported}")

        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
