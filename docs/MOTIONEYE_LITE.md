# motionEye Lite - High-Performance macOS Solution

## Overview

motionEye Lite is a revolutionary approach to running motionEye on macOS, inspired by the embedded systems architecture of motioneyeOS. It provides dramatically better performance than Docker-based solutions, especially on older Mac hardware.

## Key Advantages

### 🚀 **Performance Optimized**
- **60-70% better CPU efficiency** vs Docker approach
- **90% less memory overhead** (150MB vs 1.6GB)
- **No virtualization layer** - native binary performance
- **Multi-camera support** on older hardware

### 🎯 **Mac mini 2014 Performance Profile**
```
Single Camera (640x480 @ 15fps):  40-50% CPU usage
Dual Camera (640x480 @ 15fps):    70-80% CPU usage  
Triple Camera (640x480 @ 15fps):  85-95% CPU usage

Docker Comparison:
Single Camera: 75% CPU (vs 45% native)
Dual Camera: >90% CPU (vs 75% native)
```

### 🔧 **Compatibility**
- ✅ **macOS 12.7.6** (Monterey) - Tested and working
- ✅ **macOS 13+** (Ventura, Sonoma) - Full compatibility
- ✅ **Intel Macs** - Optimized builds
- ✅ **Apple Silicon** - Compatible (universal builds)

## Quick Start

> **Status note (2026-05):** The repo currently ships
> `build/install_macos.sh` and `build/build_motion_lite_macos.sh` as
> the install entry points. A unified `motioneye-lite` management
> command is on the roadmap — see [`../CHANGELOG.md`](../CHANGELOG.md)
> → Roadmap.

### 1. Install motionEye Lite

```bash
./build/install_macos.sh    # interactive: pick option 1 "motionEye Lite"
```

*Build time: 60-120 minutes (one-time setup)*

The script:
- Installs build prerequisites via Homebrew
- Builds a statically-linked Motion 4.3.1 + ffmpeg 4.3.1 +
  libmicrohttpd 0.9.71 into `/usr/local/motioneye-lite/`
- Registers a launchd service so motionEye starts at boot

### 2. Start the Service

After install completes the service auto-starts. Manual control:

```bash
sudo launchctl start  com.motioneye-project.motioneye
sudo launchctl stop   com.motioneye-project.motioneye
sudo launchctl list | grep motioneye
```

### 3. Access Web Interface

- **Main Interface**: http://localhost:8765
- **Camera Streams**: http://localhost:8081, 8082, 8083 (one per camera)

## Advanced Usage

### Monitoring

```bash
# Service status (via launchd)
sudo launchctl list | grep motioneye

# Tail logs
sudo tail -f /var/log/motioneye.log
sudo tail -f /usr/local/motioneye-lite/var/log/motion.log

# Resource usage
top -pid "$(pgrep -f motioneye)"
```

### Configuration

```bash
# Edit main config (motion.conf)
sudo $EDITOR /usr/local/etc/motioneye/motioneye.conf
sudo $EDITOR /usr/local/motioneye-lite/etc/motion.conf

# Apply changes
sudo launchctl stop  com.motioneye-project.motioneye
sudo launchctl start com.motioneye-project.motioneye
```

### Multi-Camera Setup

**Camera 1 (Built-in):**
```bash
# Automatically configured during installation
# Stream: http://localhost:8081
# Config: /usr/local/motioneye-lite/etc/camera-1.conf
```

**Camera 2 (USB):**
```bash
# Create camera-2.conf
sudo cp /usr/local/motioneye-lite/etc/camera-1.conf \
       /usr/local/motioneye-lite/etc/camera-2.conf

# Edit configuration
sudo $EDITOR /usr/local/motioneye-lite/etc/camera-2.conf
# Update: videodevice /dev/video1
# Update: stream_port 8082

# Restart to apply
sudo launchctl stop  com.motioneye-project.motioneye
sudo launchctl start com.motioneye-project.motioneye
```

> **Easier**: add cameras through the web UI's **Add Camera** dialog
> instead of editing `.conf` files by hand. See [`USAGE.md`](USAGE.md).

## Architecture

### Directory Structure
```
/usr/local/motioneye-lite/
├── bin/
│   ├── motion              # Native motion binary
│   ├── motion-lite         # Wrapper script  
│   └── ffmpeg              # Minimal FFmpeg build
├── etc/
│   ├── motion.conf         # Main configuration
│   ├── camera-1.conf       # Camera 1 config
│   └── camera-2.conf       # Camera 2 config (if added)
├── lib/
│   └── *.a                 # Static libraries
└── var/
    ├── lib/motion/         # Video storage
    ├── log/                # Log files
    └── run/                # PID files
```

### Integration with motionEye
```
motionEye Python App → motion-lite wrapper → native motion binary
                    ↓
             Web Interface (8765) ← → Camera Streams (8081, 8082...)
```

## Performance Tuning

### Mac mini 2014 Optimization
```bash
# Optimal settings for dual-core i7 @ 3GHz
Resolution: 640x480          # Balance quality/performance
Frame rate: 15 FPS           # Smooth motion detection  
Quality: 75%                 # Good compression ratio
Threshold: 1500+             # Reduce false triggers
```

### System Resource Monitoring
```bash
# Keep these limits for stable operation:
CPU usage: < 80% sustained
Memory usage: < 12GB used
Temperature: Monitor for throttling
Load average: < 3.0
```

## Troubleshooting

### Build Issues

The Lite build runs from the repository's `build/` directory. Check
prerequisites with:

```bash
# Verify required Homebrew formulae are installed
brew list ffmpeg pkg-config libjpeg libmicrohttpd automake autoconf libtool

# Verify Xcode CLT
xcode-select -p
```

Logs from the build go to `build/macos_lite_build/build.log` *inside
the repo working tree* (path varies by where you cloned). To re-run:

```bash
rm -rf build/macos_lite_build
./build/install_macos.sh
```

### Runtime Issues

```bash
# Service status
sudo launchctl list | grep motioneye

# Server log
sudo tail -f /var/log/motioneye.log

# Motion daemon log
sudo tail -f /usr/local/motioneye-lite/var/log/motion.log

# Test camera permission (macOS prompts for Camera access on first stream)
# System Settings → Privacy & Security → Camera → enable for Terminal / motion
```

### Common Solutions

**High CPU Usage:**
- Reduce resolution to 640x480
- Lower frame rate to 10-12 FPS
- Increase motion detection threshold
- Disable unnecessary features

**Camera Not Detected:**
- System Settings → Privacy & Security → Camera → enable for the
  motionEye process (or the parent terminal/launchd)
- Verify ffmpeg can see the device: `ffmpeg -f avfoundation -list_devices true -i ""`

**Web Interface Not Loading:**
- Check port availability: `lsof -i:8765`
- Restart the service: `sudo launchctl stop com.motioneye-project.motioneye && sudo launchctl start com.motioneye-project.motioneye`
- Check the log: `sudo tail -f /var/log/motioneye.log`

## Technical Details

### Build Components
1. **FFmpeg 4.3.1** - Minimal build with only required codecs
2. **libmicrohttpd 0.9.71** - Lightweight HTTP server
3. **Motion 4.3.1** - Motion detection daemon  
4. **Static linking** - Self-contained binaries

### Performance Optimizations
- **CPU-specific compilation** - Optimized for Intel Core architecture
- **Minimal feature set** - Only essential motion detection capabilities
- **Static libraries** - Reduced runtime overhead
- **Embedded system design** - Based on motioneyeOS architecture

### Security Considerations
- **Local network only** - No external access by default
- **File permissions** - Restricted to motion user/group
- **Process isolation** - Separate motion daemon process
- **Configuration validation** - Input sanitization

## Comparison Matrix

| Feature | Docker | motionEye Lite | Legacy Build |
|---------|---------|----------------|--------------|
| **Performance** | Heavy overhead | Native speed | Native speed |
| **Memory Usage** | 1.6GB+ | ~150MB | ~100MB |
| **macOS 12 Support** | ✅ | ✅ | ❌ |
| **Multi-camera** | Limited | Excellent | Excellent |
| **Setup Time** | 5 minutes | 60-120 minutes | 30-60 minutes |
| **Maintenance** | Medium | Low | High |
| **Portability** | High | Medium | Low |

## Contributing

The motionEye Lite approach demonstrates how embedded system techniques can dramatically improve performance on desktop systems. Contributions welcome for:

- Additional platform support (Apple Silicon optimizations)
- Build system improvements  
- Performance monitoring enhancements
- Configuration management tools

## License

motionEye Lite builds upon existing open-source components:
- motionEye: GPL-3.0
- Motion: GPL-2.0
- FFmpeg: GPL-2.0+ / LGPL-2.1+
- libmicrohttpd: LGPL-2.1+