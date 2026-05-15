# Installation Guide

Three install paths, pick one:

1. **[Docker](#docker)** — recommended for almost everyone. Cross-platform,
   bundled Motion daemon, simple upgrades.
2. **[Linux native](#linux-native)** — `pip install motioneye` with the
   distro's Motion package. Best for headless servers and Pi.
3. **[macOS native](#macos-native)** — required for USB-camera support
   on macOS (Docker Desktop can't pass AVFoundation devices through).

For Windows, see [Windows](#windows) below.

---

## System requirements

| Tier | CPU | RAM | Storage |
|---|---|---|---|
| Minimum | 1 GHz x86-64 / ARM64 | 512 MB | 1 GB |
| Recommended (multi-camera HD) | Quad-core 2 GHz+ | 2 GB+ | 10 GB+ |

**Software prerequisites depend on the install path** — see the
relevant section below. Docker is the lightest.

### Optional Python extras

| Extra | Installs | Notes |
|---|---|---|
| `face_recognition` | `face_recognition`, `dlib` | Needs a C++ compiler, CMake |
| (default) | `paho-mqtt`, `boto3`, `opencv-python`, `pycurl` | Always installed |

---

## Docker

See [`DOCKER.md`](DOCKER.md) for the full guide. Quick start:

```bash
docker run -d \
  --name motioneye \
  --restart unless-stopped \
  -p 8765:8765 \
  -p 8081:8081 \
  -v motioneye-config:/etc/motioneye \
  -v motioneye-media:/var/lib/motioneye \
  -v /etc/localtime:/etc/localtime:ro \
  im1k31s/motioneye-custom:latest
```

Compose recipe and multi-arch build instructions: [`DOCKER.md`](DOCKER.md).

---

## Linux native

### Ubuntu / Debian / Raspberry Pi OS

```bash
sudo apt update
sudo apt install -y \
  python3 python3-pip python3-venv \
  motion ffmpeg v4l-utils \
  build-essential cmake pkg-config \
  libjpeg-dev libpng-dev libtiff-dev

# Virtual environment (recommended)
python3 -m venv ~/motioneye-env
source ~/motioneye-env/bin/activate

pip install --upgrade pip
pip install motioneye

# Facial recognition (optional)
pip install motioneye[face_recognition]

# First-run config + systemd unit
motioneye_init
sudo systemctl enable --now motioneye
```

### Fedora / RHEL / CentOS Stream

```bash
sudo dnf install -y python3 python3-pip motion ffmpeg v4l-utils \
  gcc cmake pkg-config libjpeg-turbo-devel
python3 -m venv ~/motioneye-env
source ~/motioneye-env/bin/activate
pip install --upgrade pip
pip install motioneye
motioneye_init
sudo systemctl enable --now motioneye
```

### Arch Linux

```bash
sudo pacman -S python python-pip motion ffmpeg v4l-utils
# Optionally: yay -S motioneye  (AUR)
# Otherwise follow the Ubuntu venv steps above
```

---

## macOS native

Two paths, pick one:

### Option A: motionEye Lite (recommended)

Native build with statically-linked Motion + ffmpeg. Best
performance, supports USB cameras. Build time 60–120 minutes
(one-time).

```bash
git clone https://github.com/M1K31/MotionEye-Custom.git
cd MotionEye-Custom

./build/install_macos.sh        # interactive, requires sudo
```

See [`MOTIONEYE_LITE.md`](MOTIONEYE_LITE.md) for details, runtime
controls, and tuning.

### Option B: Standard Homebrew install

Slower path. Build the Motion daemon via the bundled builder, then
install MotionEye via pip:

```bash
# 1. Install build prerequisites
brew install python3 cmake pkg-config openblas libjpeg libpng

# 2. Build the Motion daemon (~15-25 min)
./build/build_motion_macos.sh   # uses sudo make install -> /usr/local/bin/motion

# Or build without sudo into ~/.local/bin/motion (see notes below)

# 3. Install MotionEye
python3 -m venv ~/motioneye-env
source ~/motioneye-env/bin/activate
pip install --upgrade pip
pip install motioneye
motioneye_init
python -m motioneye.meyectl startserver
```

To build Motion without sudo into `~/.local/bin/motion`:

```bash
brew install ffmpeg autoconf automake libtool libmicrohttpd \
             pkg-config libjpeg
mkdir -p /tmp/motion-src && cd /tmp/motion-src
git clone --depth 1 https://github.com/Motion-Project/motion.git src
cd src
# macOS portability patch (ulong is a Linux-only typedef on clang)
for f in src/jpegutils.cpp src/webu_ans.cpp src/webu_ans.hpp; do
    perl -i -pe 's/\bulong\b/unsigned long/g' "$f"
done
autoreconf -fiv
PKG_CONFIG_PATH="$(brew --prefix)/lib/pkgconfig" ./configure
make -j"$(sysctl -n hw.ncpu)"
mkdir -p ~/.local/bin
cp src/motion ~/.local/bin/motion
# Ensure ~/.local/bin is on PATH
```

### Option C: Docker Desktop

Cross-platform, but **cannot access USB cameras** through Docker
Desktop's Linux VM on macOS. Fine for IP cameras only.

```bash
# Install Docker Desktop, then:
docker run -d --name motioneye -p 8765:8765 \
  -v motioneye-config:/etc/motioneye \
  -v motioneye-media:/var/lib/motioneye \
  im1k31s/motioneye-custom:latest
```

---

## Windows

Windows is supported via Docker or WSL2 — no native install.

### Docker Desktop

Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/),
then use the [Docker Quick Start](#docker) above.

### WSL2

```powershell
wsl --install
wsl --install -d Ubuntu
```

Inside Ubuntu, follow the [Ubuntu / Debian](#ubuntu--debian--raspberry-pi-os)
section.

---

## Installing the Motion daemon

The Motion daemon is required for **USB Webcam (V4L2)**, **Pi Camera
Module (MMAL)**, **Built-in / USB Camera (AVFoundation)**, and
**IP / Network Camera** options. Without it, the Add Camera dialog
falls back to **Remote motionEye** and **MJPEG Stream Proxy** only.

| Platform | Command |
|---|---|
| Ubuntu / Debian / Pi OS | `sudo apt install motion` |
| Fedora / RHEL | `sudo dnf install motion` |
| Arch | `sudo pacman -S motion` |
| macOS | `./build/install_macos.sh` (or no-sudo path above) |
| Docker | bundled in `im1k31s/motioneye-custom` |

---

## First-run setup

After installing (any path), open the web UI:

- Default URL: <http://localhost:8765/>
- First boot shows the **Set Admin Password** modal — set one and
  click Save.
- Add cameras via the **Add Camera** dialog.

See [`USAGE.md`](USAGE.md) for the operational walkthrough (cameras,
motion detection, facial recognition, Home Assistant integration,
storage, tuning).

---

## Updating

### Docker

```bash
docker pull im1k31s/motioneye-custom:latest
docker compose down && docker compose up -d
```

### Native (pip)

```bash
source ~/motioneye-env/bin/activate
pip install --upgrade motioneye
sudo systemctl restart motioneye   # Linux only
```

After major upgrades, see the **Upgrade Notes** section in
[`../CHANGELOG.md`](../CHANGELOG.md).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `which motion` shows nothing | Motion daemon not installed | See [Installing the Motion daemon](#installing-the-motion-daemon) |
| Port 8765 in use | Another service on that port | `lsof -i :8765` to identify; or change the host port mapping (Docker) |
| Permission denied for `/dev/video0` (Linux) | User not in `video` group | `sudo usermod -a -G video $USER` then re-login |
| pid directory not writable (macOS) | Default `/var/run` is root-only | Set `MOTIONEYE_RUN_PATH=/tmp/motioneye/run` |
| Motion build fails on macOS with `unknown type name 'ulong'` | Upstream uses non-portable typedef | Already patched by `build/build_motion_macos.sh`; if building manually, see Option B above |

For more: [`USAGE.md`](USAGE.md) Troubleshooting · [`DOCKER.md`](DOCKER.md) Troubleshooting

---

## Removal

See [`../UNINSTALL.md`](../UNINSTALL.md).
