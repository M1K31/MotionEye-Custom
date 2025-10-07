# Installation Guide

This guide provides comprehensive installation instructions for MotionEye Custom across different platforms and deployment methods.

## 🐳 Docker Installation (Recommended)

Docker provides the easiest and most reliable installation method across all platforms.

### Quick Start
```bash
docker run -d \
  --name motioneye \
  --restart unless-stopped \
  -p 8765:8765 \
  -v /etc/localtime:/etc/localtime:ro \
  -v motioneye-config:/etc/motioneye \
  -v motioneye-media:/var/lib/motioneye \
  m1k31/motioneye-custom:latest
```

### Docker Compose (Recommended for Production)
```yaml
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
      - /dev/video0:/dev/video0  # For USB cameras
    devices:
      - /dev/video0  # Adjust for your camera devices
```

Save as `docker-compose.yml` and run:
```bash
docker-compose up -d
```

## 🐧 Linux Installation

### Ubuntu/Debian
```bash
# Update system
sudo apt update

# Install system dependencies
sudo apt install -y python3 python3-pip python3-venv motion ffmpeg v4l-utils

# For facial recognition (optional)
sudo apt install -y build-essential cmake python3-dev libopenblas-dev liblapack-dev libjpeg-dev

# Create virtual environment
python3 -m venv motioneye-env
source motioneye-env/bin/activate

# Install MotionEye
pip install --upgrade pip
pip install motioneye

# Initialize configuration
motioneye_init

# Start service
systemctl enable motioneye
systemctl start motioneye
```

### CentOS/RHEL/Fedora
```bash
# Install dependencies
sudo dnf install python3 python3-pip motion ffmpeg v4l-utils

# Follow the same steps as Ubuntu from virtual environment creation
```

### Arch Linux
```bash
# Install from AUR or follow manual installation
yay -S motioneye

# Or manual installation
sudo pacman -S python3 python-pip motion ffmpeg v4l-utils
# Then follow Ubuntu steps
```

## 🍎 macOS Installation

### MotionEye Lite (Recommended)

MotionEye Lite provides 60-70% better performance compared to Docker on macOS by using native binaries.

```bash
# Clone repository
git clone https://github.com/M1K31/MotionEye-Custom.git
cd MotionEye-Custom

# Run installation script
./build/install_macos.sh

# Start MotionEye
/opt/motioneye-lite/bin/meyectl startserver
```

### Standard Installation
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install python3 cmake pkg-config
brew install openblas libjpeg libpng libtiff
brew install motion ffmpeg

# Create virtual environment
python3 -m venv motioneye-env
source motioneye-env/bin/activate

# Install MotionEye
pip install --upgrade pip
pip install motioneye

# Initialize and start
motioneye_init
python -m motioneye.meyectl startserver
```

### Docker on macOS
If native installation fails, Docker provides a reliable fallback:

```bash
# Install Docker Desktop for Mac
# Then use the Docker installation method above
```

## 🪟 Windows Installation

### Docker Desktop (Recommended)
1. Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
2. Use the Docker installation method above

### WSL2 (Advanced)
1. Install [WSL2](https://docs.microsoft.com/en-us/windows/wsl/install)
2. Install Ubuntu or another Linux distribution
3. Follow the Linux installation instructions inside WSL2

## 🔧 Post-Installation Configuration

### 1. Initial Setup
1. Access web interface: `http://localhost:8765`
2. Create admin account
3. Configure basic settings

### 2. Camera Configuration
- **IP Cameras:** Add via RTSP/HTTP URLs
- **USB Cameras:** Auto-detected on Linux, may need device mapping in Docker
- **Network Cameras:** Configure via manufacturer's streaming URLs

### 3. Motion Detection Setup
1. Set detection sensitivity
2. Configure recording settings
3. Set up notification preferences

### 4. Optional Features

#### Facial Recognition
```bash
# Ensure face_recognition is installed
pip install face_recognition

# Configure in web interface under Camera Settings
```

#### Home Assistant Integration
```yaml
# Add to Home Assistant configuration.yaml
camera:
  - platform: motioneye
    url: http://localhost:8765
```

### 5. Service Management

#### Linux (systemd)
```bash
# Start/stop service
sudo systemctl start motioneye
sudo systemctl stop motioneye

# Enable auto-start
sudo systemctl enable motioneye

# Check status
sudo systemctl status motioneye
```

#### macOS (launchd)
```bash
# Create launch agent (optional)
cp extras/motioneye.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/motioneye.plist
```

#### Docker
```bash
# Start/stop container
docker start motioneye
docker stop motioneye

# View logs
docker logs motioneye

# Auto-restart configuration
docker run --restart unless-stopped ...
```

## 🔍 Troubleshooting

### Common Issues

#### Permission Denied for Camera Devices
```bash
# Add user to video group (Linux)
sudo usermod -a -G video $USER

# For Docker, ensure proper device mapping
docker run --device /dev/video0 ...
```

#### Port Already in Use
```bash
# Check what's using port 8765
netstat -tulpn | grep 8765

# Use different port
docker run -p 8080:8765 ...
```

#### Motion Binary Not Found
```bash
# Install motion package
# Ubuntu/Debian
sudo apt install motion

# macOS
brew install motion

# Or use MotionEye Lite which includes embedded motion
```

### Performance Optimization

#### For Low-End Systems
- Reduce camera resolution
- Lower frame rate
- Adjust motion detection sensitivity
- Use hardware acceleration if available

#### For High-End Systems
- Enable facial recognition
- Use multiple camera streams
- Configure advanced recording options

## 📋 System Requirements

### Minimum Requirements
- **CPU:** 1GHz+ (x86-64 or ARM64)
- **RAM:** 512MB
- **Storage:** 1GB available space
- **Network:** 100Mbps for multiple IP cameras

### Recommended Requirements
- **CPU:** Quad-core 2GHz+
- **RAM:** 2GB+
- **Storage:** 10GB+ for recordings
- **Network:** 1Gbps for high-resolution cameras

## 🔐 Security Considerations

1. **Change Default Credentials:** Always create strong admin passwords
2. **Network Security:** Use HTTPS in production, configure firewall rules
3. **Camera Security:** Secure camera credentials, use VLANs if possible
4. **Updates:** Keep system and dependencies updated regularly

## 📞 Getting Help

- **Documentation:** Check all guides in the `docs/` directory
- **Issues:** [GitHub Issues](https://github.com/M1K31/MotionEye-Custom/issues)
- **Community:** [GitHub Discussions](https://github.com/M1K31/MotionEye-Custom/discussions)

For uninstallation instructions, see [UNINSTALL.md](../UNINSTALL.md).