# MotionEye Custom

[![CI - Linux](https://github.com/M1K31/MotionEye-Custom/actions/workflows/ci-linux.yml/badge.svg)](https://github.com/M1K31/MotionEye-Custom/actions/workflows/ci-linux.yml) [![CI - macOS](https://github.com/M1K31/MotionEye-Custom/actions/workflows/ci-macos.yml/badge.svg)](https://github.com/M1K31/MotionEye-Custom/actions/workflows/ci-macos.yml) [![Docker Publish](https://github.com/M1K31/MotionEye-Custom/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/M1K31/MotionEye-Custom/actions/workflows/docker-publish.yml)

**MotionEye** is a web-based frontend for [Motion](https://motion-project.github.io/), providing an elegant interface for video surveillance with motion detection, facial recognition, and advanced automation features.

This repository contains an enhanced version of motionEye with performance optimizations, improved cross-platform support, and additional features.

---

## 📋 Table of Contents

- [Requirements](#-requirements)
- [Installation](#-installation)
  - [Docker (Recommended)](#-docker-installation-recommended)
  - [Linux Native](#-linux-installation)
  - [macOS Native](#-macos-installation)
  - [Windows](#-windows-installation)
- [Usage](#-usage)
- [Uninstallation](#-uninstallation)
- [Features](#-features)
- [Compatibility](#-compatibility)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📦 Requirements

### Minimum System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | x86-64 or ARM64 | Multi-core processor |
| **RAM** | 512 MB | 2 GB+ |
| **Storage** | 1 GB free | 10 GB+ for recordings |
| **Network** | For camera access | Gigabit for multiple HD cameras |

### Software Requirements

#### For Docker Installation
- **Docker Engine** 20.10+ or Docker Desktop
- **Docker Compose** v2.0+ (optional, recommended)

#### For Native Installation
- **Python** 3.9 or higher (3.11 recommended)
- **pip** package manager
- **Motion** daemon (for camera processing)
- **FFmpeg** (for video processing)

### Optional Dependencies

| Feature | Package | Notes |
|---------|---------|-------|
| Facial Recognition | \`face_recognition\` + \`dlib\` | Requires C++ compiler, CMake |
| MQTT/Home Assistant | \`paho-mqtt\` | Included by default |
| Cloud Uploads | \`boto3\` | For S3 storage |

---

## 🚀 Installation

### 🐳 Docker Installation (Recommended)

Docker provides the easiest and most reliable installation method across all platforms.

#### Quick Start
\`\`\`bash
docker run -d \\
  --name motioneye \\
  --restart unless-stopped \\
  -p 8765:8765 \\
  -v /etc/localtime:/etc/localtime:ro \\
  -v motioneye-config:/etc/motioneye \\
  -v motioneye-media:/var/lib/motioneye \\
  m1k31/motioneye-custom:latest
\`\`\`

#### Docker Compose (Recommended for Production)

Create a \`docker-compose.yml\` file:

\`\`\`yaml
version: '3.8'
services:
  motioneye:
    image: m1k31/motioneye-custom:latest
    container_name: motioneye
    restart: unless-stopped
    ports:
      - "8765:8765"
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - ./config:/etc/motioneye
      - ./media:/var/lib/motioneye
    devices:
      - /dev/video0:/dev/video0  # For USB cameras (optional)
    environment:
      - TZ=America/New_York  # Your timezone
\`\`\`

Start the service:
\`\`\`bash
docker-compose up -d
\`\`\`

#### Building from Source
\`\`\`bash
git clone https://github.com/M1K31/MotionEye-Custom.git
cd MotionEye-Custom
docker build -t motioneye-local -f docker/Dockerfile .
docker run -d --name motioneye -p 8765:8765 motioneye-local
\`\`\`

---

### 🐧 Linux Installation

#### Ubuntu/Debian
\`\`\`bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y \\
  python3 python3-pip python3-venv \\
  motion ffmpeg v4l-utils \\
  build-essential cmake pkg-config \\
  libjpeg-dev libpng-dev libtiff-dev

# Create virtual environment
python3 -m venv ~/motioneye-env
source ~/motioneye-env/bin/activate

# Install MotionEye
pip install --upgrade pip
pip install motioneye

# For facial recognition support (optional):
pip install motioneye[face_recognition]

# Initialize configuration
motioneye_init

# Install and enable systemd service
sudo systemctl enable motioneye
sudo systemctl start motioneye
\`\`\`

#### CentOS/RHEL/Fedora
\`\`\`bash
# Install dependencies
sudo dnf install -y python3 python3-pip motion ffmpeg v4l-utils

# Create virtual environment and install
python3 -m venv ~/motioneye-env
source ~/motioneye-env/bin/activate
pip install motioneye

# Initialize and start
motioneye_init
sudo systemctl enable --now motioneye
\`\`\`

---

### 🍎 macOS Installation

#### Option 1: MotionEye Lite (Best Performance)

MotionEye Lite provides 60-70% better performance than Docker by using native binaries.

\`\`\`bash
# Clone repository
git clone https://github.com/M1K31/MotionEye-Custom.git
cd MotionEye-Custom

# Run installation script (builds native binaries)
./build/install_macos.sh

# Start MotionEye
/opt/motioneye-lite/bin/meyectl startserver
\`\`\`

**Note:** Build time is 60-120 minutes (one-time setup).

#### Option 2: Standard Python Installation

\`\`\`bash
# Install Homebrew (if not installed)
/bin/bash -c "\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 cmake pkg-config openblas libjpeg libpng motion ffmpeg

# Create virtual environment
python3 -m venv ~/motioneye-env
source ~/motioneye-env/bin/activate

# Install MotionEye
pip install --upgrade pip
pip install motioneye

# Initialize and start
motioneye_init
python -m motioneye.meyectl startserver
\`\`\`

#### Option 3: Docker Desktop
Install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/) and use the Docker installation method above.

---

### 🪟 Windows Installation

Windows installation requires Docker or WSL2.

#### Option 1: Docker Desktop (Recommended)
1. Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
2. Use the Docker installation method above

#### Option 2: WSL2
1. Install [WSL2](https://docs.microsoft.com/en-us/windows/wsl/install): \`wsl --install\`
2. Install Ubuntu or Debian from Microsoft Store
3. Follow the Linux installation instructions inside WSL2

---

## 🎮 Usage

### Accessing the Web Interface

After installation, access MotionEye at: **http://localhost:8765**

Default credentials (first-time setup):
- **Username:** \`admin\`
- **Password:** (set on first login)

### Starting and Stopping Services

#### Docker
\`\`\`bash
# Start
docker start motioneye

# Stop
docker stop motioneye

# Restart
docker restart motioneye

# View logs
docker logs -f motioneye

# Check status
docker ps -f name=motioneye
\`\`\`

#### Linux (systemd)
\`\`\`bash
# Start
sudo systemctl start motioneye

# Stop
sudo systemctl stop motioneye

# Restart
sudo systemctl restart motioneye

# Enable at boot
sudo systemctl enable motioneye

# View logs
journalctl -u motioneye -f

# Check status
sudo systemctl status motioneye
\`\`\`

#### macOS

**MotionEye Lite:**
\`\`\`bash
# Start
/opt/motioneye-lite/bin/meyectl startserver

# Start in background
nohup /opt/motioneye-lite/bin/meyectl startserver > /tmp/motioneye.log 2>&1 &

# Stop
pkill -f motioneye

# Status
pgrep -f motioneye
\`\`\`

**Standard Installation:**
\`\`\`bash
# Activate environment first
source ~/motioneye-env/bin/activate

# Start
python -m motioneye.meyectl startserver

# Stop (Ctrl+C in terminal, or)
pkill -f "motioneye.meyectl"
\`\`\`

### Basic Configuration

1. **Add Cameras:** Click the camera dropdown → "Add Camera" → Choose camera type
2. **Motion Detection:** Adjust sensitivity under "Motion Detection" settings
3. **Facial Recognition:** Navigate to Settings → Familiar Faces (requires face_recognition package)
4. **Storage:** Configure storage paths and retention policies

---

## 🗑️ Uninstallation

### Docker
\`\`\`bash
# Stop and remove container
docker stop motioneye
docker rm motioneye

# Remove image
docker rmi m1k31/motioneye-custom:latest

# Remove volumes (WARNING: deletes all data!)
docker volume rm motioneye-config motioneye-media
\`\`\`

### Linux (Native)
\`\`\`bash
# Stop service
sudo systemctl stop motioneye
sudo systemctl disable motioneye

# Use uninstall script
sudo ./build/uninstall_linux.sh

# Or manual removal:
pip uninstall motioneye
rm -rf ~/motioneye-env
sudo rm -rf /etc/motioneye
sudo rm -rf /var/lib/motioneye  # WARNING: deletes recordings!
\`\`\`

### macOS

**MotionEye Lite:**
\`\`\`bash
# Stop service
pkill -f motioneye

# Use uninstall script
sudo ./build/uninstall_macos.sh

# Or manual removal:
sudo rm -rf /opt/motioneye-lite
sudo rm -f /usr/local/bin/motioneye-lite
\`\`\`

**Standard Installation:**
\`\`\`bash
pip uninstall motioneye
rm -rf ~/motioneye-env
sudo rm -rf /etc/motioneye
\`\`\`

### Complete Cleanup
\`\`\`bash
# Configuration files
sudo rm -rf /etc/motioneye

# Media files (recordings, snapshots)
sudo rm -rf /var/lib/motioneye

# Log files
sudo rm -f /var/log/motioneye.log
\`\`\`

---

## ✨ Features

### Core Features
- 🎥 **Multi-Camera Support** - Manage unlimited IP/USB cameras
- 🔍 **Motion Detection** - Advanced algorithms with customizable sensitivity
- 📱 **Responsive Web UI** - Access from any device
- 📧 **Smart Notifications** - Email, SMS, and webhook alerts
- 🎬 **Video Recording** - Automatic recording with motion triggers
- 📸 **Snapshot Capture** - Scheduled and motion-triggered photos

### Enhanced Features (This Version)
- 🤖 **Facial Recognition** - Identify known individuals (optional)
- 🏠 **Home Assistant Integration** - Native MQTT connectivity
- ⚡ **MotionEye Lite** - High-performance macOS build
- 🐳 **Multi-Platform Docker** - ARM64 and AMD64 support
- 🔐 **Enhanced Security** - Improved authentication and rate limiting

### Supported Camera Types
- IP Cameras (RTSP, HTTP, MJPEG)
- USB/Webcams (V4L2)
- Raspberry Pi Camera Module
- Network video servers
- Custom FFMPEG sources

---

## 🔧 Compatibility

### Operating Systems

| OS | Version | Support Level |
|----|---------|---------------|
| **Ubuntu** | 20.04, 22.04, 24.04 | ✅ Full |
| **Debian** | 11, 12 | ✅ Full |
| **Fedora** | 38+ | ✅ Full |
| **CentOS/RHEL** | 8, 9 | ✅ Full |
| **macOS** | 12+ (Monterey+) | ✅ Full (Lite recommended) |
| **macOS** | 10.14-11 | ⚠️ Docker only |
| **Windows** | 10, 11 | ⚠️ Docker/WSL2 only |
| **Raspberry Pi OS** | Bullseye, Bookworm | ✅ Full |

### Python Versions

| Version | Support |
|---------|---------|
| 3.9 | ✅ Minimum required |
| 3.10 | ✅ Supported |
| 3.11 | ✅ Recommended |
| 3.12+ | ✅ Supported |

### Architecture Support

| Architecture | Native | Docker |
|--------------|--------|--------|
| x86-64 (AMD64) | ✅ | ✅ |
| ARM64 (Apple Silicon, Pi 4) | ✅ | ✅ |
| ARMv7 (Pi 3, older) | ⚠️ Limited | ✅ |

---

## 📚 Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[New Features](NEW_FEATURES.md)** - What's new in this version
- **[MotionEye Lite](docs/MOTIONEYE_LITE.md)** - High-performance macOS build
- **[Docker Deployment](docker/README.md)** - Container setup and configuration
- **[Development Guide](DEVELOPMENT.md)** - Contributing and local development
- **[Uninstall Guide](UNINSTALL.md)** - Complete removal instructions
- **[Changelog](CHANGELOG.md)** - Version history

---

## 🤝 Contributing

We welcome contributions! See our [Development Guide](DEVELOPMENT.md) for setup instructions.

Quick start:
\`\`\`bash
git clone https://github.com/M1K31/MotionEye-Custom.git
cd MotionEye-Custom
python3 -m venv motioneye_env
source motioneye_env/bin/activate
pip install -e ".[all]"
python -m pytest -v
\`\`\`

---

## 🐛 Support

- **Issues:** [GitHub Issues](https://github.com/M1K31/MotionEye-Custom/issues)
- **Discussions:** [GitHub Discussions](https://github.com/M1K31/MotionEye-Custom/discussions)
- **Original Project:** [motionEye Wiki](https://github.com/motioneye-project/motioneye/wiki)

---

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built upon the excellent [motionEye](https://github.com/motioneye-project/motioneye) project
- Powered by the [Motion](https://motion-project.github.io/) video surveillance software
- Enhanced with modern web technologies and cross-platform optimizations

---

> **Note:** This is an enhanced fork with additional features. For the official stable release, visit the [original motionEye project](https://github.com/motioneye-project/motioneye).
