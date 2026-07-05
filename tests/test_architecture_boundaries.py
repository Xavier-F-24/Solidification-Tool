import ast
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "solidification_tool"


def python_files(*parts):
    root = PACKAGE_ROOT.joinpath(*parts)
    return sorted(root.rglob("*.py"))


def imports_from(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    return imports


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_ui_uses_app_api_for_cross_layer_access(self):
        ui_roots = {
            "gui": {"solidification_tool.app_api"},
            "streamlit_app": {
                "solidification_tool.app_api",
                "solidification_tool.streamlit_app",
            },
        }

        violations = []
        for ui_root, allowed_prefixes in ui_roots.items():
            for path in python_files(ui_root):
                for imported in imports_from(path):
                    if not imported.startswith("solidification_tool."):
                        continue
                    if any(imported == prefix or imported.startswith(prefix + ".") for prefix in allowed_prefixes):
                        continue
                    violations.append(f"{path.relative_to(REPO_ROOT)} imports {imported}")

        self.assertEqual([], violations)

    def test_engine_layers_do_not_import_ui_or_visualization(self):
        engine_roots = [
            "core",
            "CET_model",
            "IMS_model",
            "PDAS_model",
            "SDAS_model",
            "heat_models",
        ]
        banned_prefixes = (
            "solidification_tool.gui",
            "solidification_tool.streamlit_app",
            "solidification_tool.visualization",
            "solidification_tool.CET_visuals",
            "solidification_tool.IMS_visuals",
            "solidification_tool.PDAS_visuals",
            "solidification_tool.SDAS_visuals",
            "solidification_tool.heat_visuals",
        )

        violations = []
        for engine_root in engine_roots:
            for path in python_files(engine_root):
                for imported in imports_from(path):
                    if imported.startswith(banned_prefixes):
                        violations.append(f"{path.relative_to(REPO_ROOT)} imports {imported}")

        self.assertEqual([], violations)

    def test_app_api_keeps_heavy_layers_lazy(self):
        path = PACKAGE_ROOT / "app_api.py"
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        top_level_imports = []

        for node in tree.body:
            if isinstance(node, ast.Import):
                top_level_imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_level_imports.append(node.module)

        heavy_prefixes = (
            "solidification_tool.core.engine",
            "solidification_tool.visualization",
            "solidification_tool.io_utils",
        )
        violations = [
            imported
            for imported in top_level_imports
            if imported.startswith(heavy_prefixes)
        ]

        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()

