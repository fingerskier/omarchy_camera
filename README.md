# omarchy_camera

Omarchy bar widget that opens the default attached camera (the built-in
device when that is the only capture node).

## Install

```sh
omarchy plugin add https://github.com/fingerskier/omarchy_camera.git --enable
```

Place it on the bar if the enable step did not:

```sh
omarchy plugin enable fingerskier.camera
```

Needs Python 3 at runtime. The widget probes V4L2 capture devices; it does
not keep a live preview open.

## Usage

The bar icon is present after enable. On load it acquires the default
camera (`/dev/videoN` with Video Capture, not a metadata node).

- Camera found: tooltip and panel show the device name.
- None found, or the device cannot be opened: the bar and panel report
  `No camera found` (or the open error) instead of hanging.

Click the icon to open the status panel. Retry re-runs the probe. Escape
closes the panel.

## Verify

```sh
python3 -m unittest discover -s tests -v
omarchy plugin validate .
python3 scripts/camera.py
```

## Out of scope

Camera picker, live preview, still capture, and video recording are
separate issues.
