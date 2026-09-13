#!/usr/bin/env python3
"""Probe and acquire the default V4L2 capture camera."""

from __future__ import annotations

import ctypes
import fcntl
import json
import os
import sys
from pathlib import Path


V4L2_CAP_VIDEO_CAPTURE = 0x00000001
V4L2_CAP_DEVICE_CAPS = 0x80000000


class v4l2_capability(ctypes.Structure):
    _fields_ = [
        ("driver", ctypes.c_char * 16),
        ("card", ctypes.c_char * 32),
        ("bus_info", ctypes.c_char * 32),
        ("version", ctypes.c_uint32),
        ("capabilities", ctypes.c_uint32),
        ("device_caps", ctypes.c_uint32),
        ("reserved", ctypes.c_uint32 * 3),
    ]


def _ior(type_: str, nr: int, size: int) -> int:
    return (2 << 30) | (size << 16) | (ord(type_) << 8) | nr


VIDIOC_QUERYCAP = _ior("V", 0, ctypes.sizeof(v4l2_capability))


def is_video_capture(info: dict) -> bool:
    capabilities = int(info.get("capabilities") or 0)
    flags = (
        int(info.get("device_caps") or 0)
        if capabilities & V4L2_CAP_DEVICE_CAPS
        else capabilities
    )
    return bool(flags & V4L2_CAP_VIDEO_CAPTURE)


def list_nodes(sysfs_root: Path) -> list[dict]:
    if not sysfs_root.is_dir():
        return []
    nodes = []
    for child in sorted(sysfs_root.iterdir(), key=lambda path: path.name):
        if not child.name.startswith("video"):
            continue
        name_file = child / "name"
        name = name_file.read_text().strip() if name_file.exists() else child.name
        nodes.append({"device": f"/dev/{child.name}", "name": name})
    return nodes


def default_query_cap(path: str) -> dict:
    fd = os.open(path, os.O_RDWR | os.O_NONBLOCK)
    try:
        cap = v4l2_capability()
        fcntl.ioctl(fd, VIDIOC_QUERYCAP, cap)
        return {
            "card": cap.card.decode(errors="replace").strip("\x00"),
            "capabilities": cap.capabilities,
            "device_caps": cap.device_caps,
        }
    finally:
        os.close(fd)


def default_open(path: str) -> int:
    return os.open(path, os.O_RDWR | os.O_NONBLOCK)


def default_close(fd: int) -> None:
    os.close(fd)


def status(
    *,
    sysfs_root=None,
    query_cap=None,
    open_device=None,
    close_device=None,
) -> dict:
    if sysfs_root is None:
        sysfs_root = Path(os.environ.get("OMARCHY_CAMERA_SYSFS", "/sys/class/video4linux"))
    else:
        sysfs_root = Path(sysfs_root)
    query_cap = query_cap or default_query_cap
    open_device = open_device or default_open
    close_device = close_device or default_close

    capture: list[dict] = []
    blocked: list[dict] = []
    for node in list_nodes(sysfs_root):
        try:
            info = query_cap(node["device"])
        except OSError as exc:
            blocked.append({**node, "error": str(exc) or type(exc).__name__})
            continue
        if not is_video_capture(info):
            continue
        name = (info.get("card") or node["name"] or "").strip() or node["name"]
        capture.append({**node, "name": name})

    if capture:
        chosen = capture[0]
        try:
            fd = open_device(chosen["device"])
            close_device(fd)
        except OSError as exc:
            return {
                "ok": False,
                "device": chosen["device"],
                "name": chosen["name"],
                "error": str(exc) or "Could not open camera",
            }
        return {
            "ok": True,
            "device": chosen["device"],
            "name": chosen["name"],
            "error": None,
        }

    if blocked:
        first = blocked[0]
        return {
            "ok": False,
            "device": first["device"],
            "name": first["name"],
            "error": first["error"],
        }
    return {"ok": False, "device": None, "name": None, "error": "No camera found"}


def main() -> int:
    print(json.dumps(status()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
