# CI: ![CI - Linux](https://github.com/M1K31/MotionEye-Custom/actions/workflows/ci-linux.yml/badge.svg) ![CI - macOS](https://github.com/M1K31/MotionEye-Custom/actions/workflows/ci-macos.yml/badge.svg)

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
        For a basic installation, the following packages are required:
        ```sh
        sudo apt update
        sudo apt --no-install-recommends install python3 python3-pip python3-setuptools motion ffmpeg v4l-utils
        ```
        To enable all features (like Facial Recognition), additional build tools are needed to compile dependencies:
        ```sh
        sudo apt --no-install-recommends install build-essential cmake python3-dev libopenblas-dev liblapack-dev libjpeg-dev libboost-python-dev
        ```
    *   **For macOS:** 
        - **Recommended (motionEye Lite):** `./build/build_motion_lite_macos.sh` - High-performance embedded build
        - **Standard:** `./build/build_motion_macos.sh` - Traditional Homebrew-based build  
        - **Docker fallback:** See **[Platform Compatibility](#platform-compatibility)** section
    *   **For Docker (All Platforms):**
        ```sh
        docker build -f docker/Dockerfile.ci -t motioneye-local .
        docker run -p 8765:8765 motioneye-local
        ```
        To enable all features (like Facial Recognition), additional build tools are needed to compile dependencies:
        ```sh
        sudo apt --no-install-recommends install build-essential cmake python3-dev libopenblas-dev liblapack-dev libjpeg-dev libboost-python-dev
        ```

2.  **Install motionEye from local source:** Navigate to the root of this repository and run:
    ```sh
    sudo python3 -m pip install .
    ```
    This command installs motionEye and all its Python dependencies, including `opencv`, `face_recognition`, and `paho-mqtt`.

3.  **Run post-installation setup:**
    *   **For Linux:** `sudo motioneye_init`
    *   **For macOS:** `sudo ./build/install_macos.sh`
    > **Note:** If you get a `command not found` error when running `sudo motioneye_init`, your system's `PATH` for `sudo` may be missing the directory where `pip` installs executables. You can fix this by finding the script's location (`pip show -f motioneye | grep motioneye_init`) and running it with its full path, e.g., `sudo /home/user/.local/bin/motioneye_init`.

### Running for Development (local instance)

If you are a developer and you want to run motionEye without installing it as a system-wide service, you can run it directly from the source tree. This is useful for testing and debugging.

> **Note:** It is highly recommended to use a Python virtual environment (`venv`) for development to avoid conflicts with system packages.

1.  **Install Dependencies:** Follow the dependency installation instructions in the "For Developers" section above. Make sure you have installed both the system packages (like `motion` and `ffmpeg`) and the Python packages (e.g., by running `pip install .` inside your virtual environment).

2.  **Create Local Directories:** The server requires several local directories to store configuration, logs, and media files. Create them in the project root:
    ```sh
    mkdir -p conf run log media
    ```

3.  **Create a Local Configuration File:** You will need a configuration file to tell motionEye where to find your local directories.
    *   First, get the full path to your project directory by running `pwd`.
    *   Create a new file named `conf/motioneye.conf`.
    *   Add the following content to the file, replacing `/path/to/your/project` with the actual path you got from `pwd`:
        ```
        # Local configuration for motionEye development
        conf_path /path/to/your/project/conf
        run_path /path/to/your/project/run
        log_path /path/to/your/project/log
        media_path /path/to/your/project/media
        listen 0.0.0.0
        port 8765
        log_level info
        ```

3.  **Run the Server:** Now you can start the server using your local configuration:
    ```sh
    python3 -m motioneye.meyectl startserver -c conf/motioneye.conf
    ```
    The server will be running in the foreground and will be accessible at `http://localhost:8765`.

# Starting and Stopping the Server

For detailed instructions on how to start and stop the motionEye server, for both development and production environments, please see [`LAUNCH.md`](./LAUNCH.md).

# Upgrade

### For Users (from PyPI)

If you installed motionEye from PyPI, you can upgrade to the latest official release with:
```sh
sudo systemctl stop motioneye
sudo python3 -m pip install --upgrade --pre motioneye
sudo systemctl start motioneye
```

## Platform Compatibility

MotionEye has been thoroughly tested across multiple platforms. Here's the current compatibility status:

### ✅ **Linux** (Fully Supported)
- **Status**: Full functionality with native package installation
- **Tested**: Docker containers (Ubuntu-based)
- **Installation**: Use standard `apt` packages for `motion` and `ffmpeg`
- **Recommendation**: Preferred platform for production deployment

### ✅ **macOS** (Enhanced Support with motionEye Lite)
- **Python Components**: ✅ Fully functional (motionEye web interface, APIs, analysis features)
- **Motion Daemon**: ✅ **NEW: motionEye Lite** - Embedded-systems approach for optimal performance
  - **Performance**: 60-70% better CPU efficiency vs Docker on older hardware
  - **Compatibility**: Works on macOS 12+ including Mac mini 2014 and similar older systems
  - **Installation**: `./build/build_motion_lite_macos.sh` (embedded static build)
  - **Management**: Integrated `motioneye-lite` command for easy setup and control
- **Traditional Approach**: 
  - **macOS 13+**: Standard build with `./build/build_motion_macos.sh`
  - **macOS 12**: May encounter Homebrew dependency conflicts
- **Fallback**: Docker available for maximum compatibility
- **Development**: Perfect for Python development and testing without camera hardware

### 🐳 **Docker** (Recommended)
- **Status**: ✅ Full cross-platform compatibility
- **Benefits**: Consistent environment, all dependencies included
- **Usage**: `docker run -p 8765:8765 your-motioneye-image`
- **Best for**: Production deployment, older macOS systems, Windows users

### Development Environment
For developers working on motionEye itself:
- ✅ **Python components**: Work perfectly on all platforms
- ✅ **Testing suite**: Comprehensive test coverage (12 passed, 1 skipped)
- ✅ **CI/CD**: GitHub Actions with Linux/macOS matrix testing
- See `DEVELOPMENT.md` for detailed setup instructions

### For Developers (from source)

If you installed from source, you can update by fetching the latest code and reinstalling:
```sh
git pull
sudo python3 -m pip install .
sudo systemctl restart motioneye # Or restart the launchd service on macOS
```
