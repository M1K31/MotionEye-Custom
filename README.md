# MotionEye Custom

[![CI - Linux](https://github.com/M1K31/MotionEye-Custom/actions/workflows/ci-linux.yml/badge.svg)](https://github.com/M1K31/MotionEye-Custom/actions/workflows/ci-linux.yml) [![CI - macOS](https://github.com/M1K31/MotionEye-Custom/actions/workflows/ci-macos.yml/badge.svg)](https://github.com/M1K31/MotionEye-Custom/actions/workflows/ci-macos.yml) [![Docker Publish](https://github.com/M1K31/MotionEye-Custom/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/M1K31/MotionEye-Custom/actions/workflows/docker-publish.yml)

**MotionEye** is a web-based frontend for [Motion](https://motion-project.github.io/), providing an elegant interface for video surveillance with motion detection, facial recognition, and advanced automation features.

This repository contains an enhanced version of motionEye with performance optimizations, improved cross-platform support, and additional features.

## 🚀 Quick Start

### Docker (Recommended)

```bash
docker run -d \
  --name motioneye \
  -p 8765:8765 \
  -v /etc/localtime:/etc/localtime:ro \
  m1k31/motioneye-custom:latest
```

### Native Installation

#### Linux (Ubuntu/Debian)
```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip motion ffmpeg v4l-utils

# Install motionEye
pip3 install --user motioneye
motioneye_init
```

#### macOS (MotionEye Lite - Recommended)
```bash
# High-performance embedded build (60-70% better performance)
./build/install_macos.sh
```

#### Windows
Use Docker Desktop or WSL2 with the Linux installation method.

## 📋 System Requirements

- **CPU:** x86-64 or ARM64 (Apple Silicon supported)
- **RAM:** Minimum 512MB, recommended 2GB+
- **Storage:** 1GB+ available space
- **OS:** Linux, macOS 10.14+, Windows 10+ (via Docker)
- **Network:** For remote camera access and web interface

## ✨ Features

### Core Features
- 🎥 **Multi-Camera Support** - Manage unlimited IP/USB cameras
- 🔍 **Motion Detection** - Advanced algorithms with customizable sensitivity
- 📱 **Responsive Web UI** - Access from any device with a web browser
- 📧 **Smart Notifications** - Email, SMS, and webhook alerts
- 🎬 **Video Recording** - Automatic recording with motion triggers
- 📸 **Snapshot Capture** - Scheduled and motion-triggered photos

### Enhanced Features (This Version)
- 🤖 **Facial Recognition** - Identify known individuals automatically
- 🏠 **Home Assistant Integration** - Native smart home connectivity
- ⚡ **MotionEye Lite** - High-performance embedded build for macOS
- 🐳 **Multi-Platform Docker** - ARM64 and AMD64 support
- 📊 **Performance Monitoring** - Real-time system metrics
- 🔐 **Enhanced Security** - Improved authentication and access controls

### Supported Camera Types
- IP Cameras (RTSP, HTTP, MJPEG)
- USB/Webcams (V4L2)
- Raspberry Pi Camera Module
- Network video servers
- Custom FFMPEG sources

## 📚 Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[New Features](NEW_FEATURES.md)** - What's new in this version
- **[MotionEye Lite](docs/MOTIONEYE_LITE.md)** - High-performance macOS build
- **[Docker Deployment](docker/README.md)** - Container setup and configuration
- **[Development Guide](DEVELOPMENT.md)** - Contributing and local development
- **[Uninstall Guide](UNINSTALL.md)** - Complete removal instructions

## 🎮 Server Management

### Starting/Stopping MotionEye

#### Docker
```bash
# Start container
docker start motioneye
# or run new container
docker run -d --name motioneye -p 8765:8765 m1k31/motioneye-custom:latest

# Stop container
docker stop motioneye

# Restart container
docker restart motioneye

# View logs
docker logs motioneye
```

#### Linux (Native)
```bash
# Start service (systemd)
sudo systemctl start motioneye

# Stop service
sudo systemctl stop motioneye

# Restart service
sudo systemctl restart motioneye

# Enable auto-start at boot
sudo systemctl enable motioneye

# Check status
sudo systemctl status motioneye
```

#### macOS (MotionEye Lite)
```bash
# Start server
/opt/motioneye-lite/bin/meyectl startserver

# Stop server (Ctrl+C in terminal or kill process)
pkill -f motioneye

# Start in background
nohup /opt/motioneye-lite/bin/meyectl startserver > /tmp/motioneye.log 2>&1 &
```

#### macOS (Standard Installation)
```bash
# Activate virtual environment first
source motioneye-env/bin/activate

# Start server
python -m motioneye.meyectl startserver

# Stop server (Ctrl+C in terminal)
# For background process:
pkill -f "motioneye.meyectl startserver"
```

## 🔧 Configuration

After starting the server, access the web interface at `http://localhost:8765` (default).

### Initial Setup
1. Create admin account on first launch
2. Add cameras via the web interface
3. Configure motion detection settings
4. Set up notifications and recording preferences

### Advanced Configuration
- Motion detection tuning
- Facial recognition training
- Custom automation scripts
- Network and security settings

## 🤝 Contributing

We welcome contributions! See our [Development Guide](DEVELOPMENT.md) for:
- Setting up the development environment
- Running tests and code quality checks
- Submitting pull requests
- Reporting issues and bugs

## 🐛 Support

- **Issues:** [GitHub Issues](https://github.com/M1K31/MotionEye-Custom/issues)
- **Discussions:** [GitHub Discussions](https://github.com/M1K31/MotionEye-Custom/discussions)
- **Original Project:** [motionEye Wiki](https://github.com/motioneye-project/motioneye/wiki)

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built upon the excellent [motionEye](https://github.com/motioneye-project/motioneye) project
- Powered by the [Motion](https://motion-project.github.io/) video surveillance software
- Enhanced with modern web technologies and cross-platform optimizations

---

> **Note:** This is an enhanced fork with additional features. For the official stable release, visit the [original motionEye project](https://github.com/motioneye-project/motioneye).