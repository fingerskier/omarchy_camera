import json
import os
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
import sys

sys.path.insert(0, str(SCRIPTS))
import camera


V4L2_CAP_DEVICE_CAPS = 0x80000000
V4L2_CAP_VIDEO_CAPTURE = 0x00000001
V4L2_CAP_META_CAPTURE = 0x00800000


def _sysfs(root: Path, nodes: dict[str, str]) -> Path:
    video = root / "class" / "video4linux"
    video.mkdir(parents=True)
    for name, card in nodes.items():
        node = video / name
        node.mkdir()
        (node / "name").write_text(card + "\n")
        (node / "index").write_text(name.replace("video", "") + "\n")
    return video


class CameraStatusTests(unittest.TestCase):
    def test_reports_no_camera_when_sysfs_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            sysfs = Path(directory) / "class" / "video4linux"
            sysfs.mkdir(parents=True)
            result = camera.status(sysfs_root=sysfs)
        self.assertEqual(
            result,
            {
                "ok": False,
                "device": None,
                "name": None,
                "error": "No camera found",
            },
        )

    def test_skips_metadata_nodes_and_reports_no_camera(self):
        with tempfile.TemporaryDirectory() as directory:
            sysfs = _sysfs(
                Path(directory),
                {"video1": "HD User Facing: HD User Facing"},
            )

            def query_cap(path: str):
                return {
                    "card": "HD User Facing: HD User Facing",
                    "capabilities": V4L2_CAP_DEVICE_CAPS | V4L2_CAP_META_CAPTURE,
                    "device_caps": V4L2_CAP_META_CAPTURE,
                }

            result = camera.status(
                sysfs_root=sysfs,
                query_cap=query_cap,
                open_device=lambda path: 3,
                close_device=lambda fd: None,
            )
        self.assertEqual(result["ok"], False)
        self.assertEqual(result["error"], "No camera found")
        self.assertIsNone(result["device"])

    def test_acquires_the_only_capture_device(self):
        with tempfile.TemporaryDirectory() as directory:
            sysfs = _sysfs(
                Path(directory),
                {
                    "video0": "HD User Facing: HD User Facing",
                    "video1": "HD User Facing: HD User Facing",
                },
            )
            opened = []

            def query_cap(path: str):
                if path.endswith("video0"):
                    return {
                        "card": "HD User Facing: HD User Facing",
                        "capabilities": V4L2_CAP_DEVICE_CAPS
                        | V4L2_CAP_VIDEO_CAPTURE
                        | V4L2_CAP_META_CAPTURE,
                        "device_caps": V4L2_CAP_VIDEO_CAPTURE,
                    }
                return {
                    "card": "HD User Facing: HD User Facing",
                    "capabilities": V4L2_CAP_DEVICE_CAPS
                    | V4L2_CAP_VIDEO_CAPTURE
                    | V4L2_CAP_META_CAPTURE,
                    "device_caps": V4L2_CAP_META_CAPTURE,
                }

            def open_device(path: str):
                opened.append(path)
                return 7

            result = camera.status(
                sysfs_root=sysfs,
                query_cap=query_cap,
                open_device=open_device,
                close_device=lambda fd: None,
            )
        self.assertEqual(
            result,
            {
                "ok": True,
                "device": "/dev/video0",
                "name": "HD User Facing: HD User Facing",
                "error": None,
            },
        )
        self.assertIn("/dev/video0", opened)

    def test_permission_denied_is_reported_instead_of_hanging(self):
        with tempfile.TemporaryDirectory() as directory:
            sysfs = _sysfs(Path(directory), {"video0": "Integrated Camera"})

            def query_cap(path: str):
                raise PermissionError("Permission denied")

            result = camera.status(sysfs_root=sysfs, query_cap=query_cap)
        self.assertFalse(result["ok"])
        self.assertEqual(result["device"], "/dev/video0")
        self.assertEqual(result["name"], "Integrated Camera")
        self.assertIn("Permission denied", result["error"])


class CameraCliTests(unittest.TestCase):
    def test_cli_prints_json_status(self):
        import subprocess

        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "camera.py")],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "OMARCHY_CAMERA_SYSFS": "/no/such/video4linux"},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["ok"], False)
        self.assertEqual(payload["error"], "No camera found")


if __name__ == "__main__":
    unittest.main()
