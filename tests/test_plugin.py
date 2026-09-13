import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PluginContractTests(unittest.TestCase):
    def test_manifest_declares_an_installable_bar_widget(self):
        manifest = json.loads((ROOT / "manifest.json").read_text())
        self.assertEqual(manifest["schemaVersion"], 1)
        self.assertEqual(manifest["id"], "fingerskier.camera")
        self.assertIn("bar-widget", manifest["kinds"])
        entry = manifest["entryPoints"]["barWidget"]
        self.assertTrue((ROOT / entry).is_file(), entry)
        self.assertEqual(manifest["barWidget"]["defaultSection"], "right")
        self.assertFalse(manifest["barWidget"]["allowMultiple"])

    def test_bar_widget_probes_the_default_camera_and_reports_none_found(self):
        qml = (ROOT / "plugin" / "BarWidget.qml").read_text()
        self.assertIn('moduleName: "fingerskier.camera"', qml)
        self.assertIn("scripts/camera.py", qml)
        self.assertIn("No camera found", qml)
        self.assertIn("Ui.Panel", qml)


class PluginValidateTests(unittest.TestCase):
    def test_omarchy_plugin_validate_accepts_the_folder(self):
        proc = subprocess.run(
            ["omarchy", "plugin", "validate", str(ROOT)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
