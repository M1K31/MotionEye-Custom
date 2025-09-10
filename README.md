# What is motionEye?

**motionEye** is an online interface for the software [_motion_](https://motion-project.github.io/), a video surveillance program with motion detection.

Check out the [__wiki__](https://github.com/motioneye-project/motioneye/wiki) for more details. Changelog is available on the [__releases page__](https://github.com/motioneye-project/motioneye/releases).

From version 0.43, **motionEye** is multilingual:

| [![](https://hosted.weblate.org/widgets/motioneye-project/-/287x66-black.png)<br>![](https://hosted.weblate.org/widgets/motioneye-project/-/multi-auto.svg)](https://hosted.weblate.org/engage/motioneye-project/) |
| -: |

You can contribute to translations on [__Weblate__](https://hosted.weblate.org/projects/motioneye-project).

# Installation

This repository contains a development version of motionEye with new features. The instructions below are for installing this version from the local source code.

**For instructions on how to install the official, stable release of motionEye, please refer to the [official project wiki](https://github.com/motioneye-project/motioneye/wiki).**

For a guide on the new features in this version, please see [`NEW_FEATURES.md`](./NEW_FEATURES.md).

### For Developers (installing from this source code)

These instructions will install the version of motionEye from your local checkout. For uninstallation instructions, see [`UNINSTALL.md`](./UNINSTALL.md).

1.  **Install Dependencies:**
    *   **For Linux (Debian/Ubuntu):**
        ```sh
        sudo apt update
        sudo apt --no-install-recommends install python3 python3-pip motion ffmpeg v4l-utils
        ```
    *   **For macOS:** Follow the detailed instructions in the **[macOS Installation guide](./NEW_FEATURES.md#1-macos-installation)** to build the `motion` dependency.

2.  **Install motionEye from local source:** Navigate to the root of this repository and run:
    ```sh
    sudo python3 -m pip install .
    ```
    This command installs motionEye and all its Python dependencies, including `opencv`, `face_recognition`, and `paho-mqtt`.

3.  **Run post-installation setup:**
    *   **For Linux:** `sudo motioneye_init`
    *   **For macOS:** `sudo ./build/install_macos.sh`

# Upgrade

### For Users (from PyPI)

If you installed motionEye from PyPI, you can upgrade to the latest official release with:
```sh
sudo systemctl stop motioneye
sudo python3 -m pip install --upgrade --pre motioneye
sudo systemctl start motioneye
```

### For Developers (from source)

If you installed from source, you can update by fetching the latest code and reinstalling:
```sh
git pull
sudo python3 -m pip install .
sudo systemctl restart motioneye # Or restart the launchd service on macOS
```
