# MotionEye Custom

[![CI](https://github.com/M1K31/MotionEye-Custom/actions/workflows/ci.yml/badge.svg)](https://github.com/M1K31/MotionEye-Custom/actions/workflows/ci.yml)
[![Docker Publish](https://github.com/M1K31/MotionEye-Custom/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/M1K31/MotionEye-Custom/actions/workflows/docker-publish.yml)

A custom fork of [motionEye](https://github.com/motioneye-project/motioneye) —
a web frontend for the [Motion](https://motion-project.github.io/) video
surveillance daemon — with hardened security, cross-platform camera
discovery, optional facial recognition, and Home Assistant integration.

> Looking for upstream? See the [official motionEye project](https://github.com/motioneye-project/motioneye).

---

## Quick start (Docker)

```bash
docker run -d \
  --name motioneye \
  --restart unless-stopped \
  -p 8765:8765 \
  -v motioneye-config:/etc/motioneye \
  -v motioneye-media:/var/lib/motioneye \
  im1k31s/motioneye-custom:latest
```

Then open <http://localhost:8765/> — you'll be prompted to set the admin
password on first boot.

For native install (Linux, macOS, Windows/WSL2) and the full Docker
Compose recipe, see [`docs/INSTALLATION.md`](docs/INSTALLATION.md).

---

## Features

- 🎥 **Multi-camera** support — USB/V4L2, IP/RTSP, MJPEG, Pi CSI/MMAL,
  macOS AVFoundation, and remote-motionEye relays
- 🔍 **Motion detection** with configurable sensitivity, masks, and
  scheduling
- 🤖 **Facial recognition** (optional, via `face_recognition`) — tag
  familiar faces, log unfamiliar ones
- 🏠 **Home Assistant** native integration via MQTT discovery
- 📧 Email, webhook, and Telegram notifications
- 🐳 Multi-architecture Docker images (amd64 + arm64)
- 🔐 Hardened security: bcrypt passwords, XSRF, strict CSP, TLS
  verification always enforced — see `CHANGELOG.md` for the full
  audit log

### Supported camera types

The Add Camera dialog auto-detects host capabilities and only shows
options that actually work. Labels carry the friendly name with the
technical backend in parentheses.

| User-facing option | Backend | macOS | Linux (any) | Raspberry Pi | Needs Motion daemon? |
|---|---|---|---|---|---|
| Built-in or USB Camera | AVFoundation (via ffmpeg) | ✅ | — | — | ✅ |
| USB Webcam | V4L2 | — | ✅ | ✅ | ✅ |
| Raspberry Pi Camera Module | MMAL | — | — | ✅ | ✅ |
| IP / Network Camera | RTSP / HTTP / ONVIF | ✅ | ✅ | ✅ | ✅ |
| Remote motionEye Camera | HTTP relay | ✅ | ✅ | ✅ | — |
| MJPEG Stream Proxy | direct passthrough | ✅ | ✅ | ✅ | — |

---

## Documentation

| Doc | What it covers |
|---|---|
| [`docs/INSTALLATION.md`](docs/INSTALLATION.md) | All install paths (Docker, Linux, macOS, Windows) |
| [`docs/USAGE.md`](docs/USAGE.md) | Day-to-day operation: cameras, motion detection, faces, Home Assistant, storage, tuning |
| [`docs/DOCKER.md`](docs/DOCKER.md) | Docker deployment — build, compose, devices, troubleshooting |
| [`docs/MOTIONEYE_LITE.md`](docs/MOTIONEYE_LITE.md) | High-performance native macOS build |
| [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) | Local dev setup, testing, architecture, debugging |
| [`UNINSTALL.md`](UNINSTALL.md) | Complete removal per platform |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history and roadmap |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | PR process and code style |

---

## Compatibility

| OS | Support |
|---|---|
| Ubuntu 20.04 / 22.04 / 24.04, Debian 11 / 12 | ✅ Full |
| Fedora 38+, RHEL 8 / 9 | ✅ Full |
| Raspberry Pi OS (Bullseye, Bookworm) | ✅ Full |
| macOS 12+ (Monterey or newer) | ✅ Full (Lite recommended) |
| Windows 10 / 11 | ⚠️ Docker or WSL2 |

| Python | Status |
|---|---|
| 3.9 | ✅ Minimum |
| 3.11 | ✅ Recommended (CI target) |
| 3.13 | ✅ Supported (CI target) |

| Architecture | Native | Docker |
|---|---|---|
| x86_64 / amd64 | ✅ | ✅ |
| arm64 (Apple Silicon, Pi 4/5) | ✅ | ✅ |
| armv7 (Pi 3 and older) | ⚠️ Limited | ✅ |

---

## Contributing

```bash
git clone https://github.com/M1K31/MotionEye-Custom.git
cd MotionEye-Custom
make dev-install      # bootstraps motioneye_env/ and installs deps
make test
```

See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for setup details and
[`CONTRIBUTING.md`](CONTRIBUTING.md) for the PR workflow.

---

## License

GPL-3.0 — see [`LICENSE`](LICENSE).

## Acknowledgments

Built on the excellent [motionEye](https://github.com/motioneye-project/motioneye)
project and the [Motion](https://motion-project.github.io/) daemon.
