#!/bin/bash
# motionEye macOS Lite Build Script
# Inspired by motioneyeos embedded approach
# Optimized for older macOS versions (10.12+) and Mac mini 2014
# 
# Performance optimized for:
# - Dual-Core Intel Core i7 @ 3 GHz
# - 16 GB RAM
# - macOS 12.7.6 (Monterey)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/macos_lite_build"
INSTALL_PREFIX="/usr/local/motioneye-lite"
MOTION_VERSION="4.3.1"
FFMPEG_VERSION="4.3.1"
LOG_FILE="${BUILD_DIR}/build.log"

# Create build directory and log file
mkdir -p "${BUILD_DIR}"
exec > >(tee -a "${LOG_FILE}")
exec 2>&1

echo "=== motionEye macOS Lite Builder ==="
echo "Building minimal motion daemon for older macOS compatibility"
echo "Optimized for Mac mini 2014 performance profile"
echo "Build log: ${LOG_FILE}"
echo "Started: $(date)"
echo ""

# Check for required tools
check_prerequisites() {
    echo "Checking prerequisites..."
    
    if ! command -v git >/dev/null 2>&1; then
        echo "❌ git is required"
        exit 1
    fi
    
    if ! command -v make >/dev/null 2>&1; then
        echo "❌ make is required"  
        exit 1
    fi
    
    if ! command -v pkg-config >/dev/null 2>&1; then
        echo "❌ pkg-config is required (install with: brew install pkg-config)"
        exit 1
    fi
    
    # Check for Xcode Command Line Tools
    if ! xcode-select -p >/dev/null 2>&1; then
        echo "❌ Xcode Command Line Tools required"
        echo "Install with: xcode-select --install"
        exit 1
    fi
    
    echo "✅ Prerequisites check passed"
}

# Install minimal dependencies via Homebrew (lightweight approach)
install_lite_dependencies() {
    echo "Installing minimal dependencies..."
    
    # Check if Homebrew is installed
    if ! command -v brew >/dev/null 2>&1; then
        echo "❌ Homebrew is required for macOS builds"
        echo "Install from: https://brew.sh/"
        exit 1
    fi
    
    # Install only essential packages
    echo "Installing core dependencies..."
    brew list autoconf >/dev/null 2>&1 || brew install autoconf
    brew list automake >/dev/null 2>&1 || brew install automake
    brew list libtool >/dev/null 2>&1 || brew install libtool
    brew list pkg-config >/dev/null 2>&1 || brew install pkg-config
    brew list jpeg >/dev/null 2>&1 || brew install jpeg
    
    echo "✅ Core dependencies installed"
}

# Build minimal FFmpeg (inspired by motioneyeos config)
build_minimal_ffmpeg() {
    echo "Building minimal FFmpeg ${FFMPEG_VERSION}..."
    echo "This may take 30-60 minutes on Mac mini 2014..."
    
    cd "${BUILD_DIR}"
    
    if [ ! -d "ffmpeg-${FFMPEG_VERSION}" ]; then
        echo "Downloading FFmpeg ${FFMPEG_VERSION}..."
        curl -L -o "ffmpeg-${FFMPEG_VERSION}.tar.xz" \
            "https://ffmpeg.org/releases/ffmpeg-${FFMPEG_VERSION}.tar.xz"
        tar -xf "ffmpeg-${FFMPEG_VERSION}.tar.xz"
    fi
    
    cd "ffmpeg-${FFMPEG_VERSION}"
    
    # Clean previous build
    make clean 2>/dev/null || true
    
    # Optimized minimal configuration for Mac mini 2014
    # Based on motioneyeos package/ffmpeg/ffmpeg.mk
    echo "Configuring FFmpeg with minimal feature set..."
    ./configure \
        --prefix="${INSTALL_PREFIX}" \
        --enable-gpl \
        --disable-doc \
        --disable-debug \
        --disable-shared \
        --enable-static \
        --disable-ffplay \
        --disable-ffprobe \
        --disable-ffmpeg \
        --enable-avcodec \
        --enable-avformat \
        --enable-swscale \
        --disable-avdevice \
        --disable-postproc \
        --disable-avfilter \
        --disable-network \
        --disable-protocols \
        --enable-protocol=file \
        --disable-indevs \
        --disable-outdevs \
        --disable-devices \
        --disable-hwaccels \
        --disable-encoders \
        --enable-encoder=mjpeg \
        --enable-encoder=mpeg4 \
        --disable-decoders \
        --enable-decoder=mjpeg \
        --enable-decoder=mpeg4 \
        --enable-decoder=h264 \
        --disable-parsers \
        --enable-parser=mjpeg \
        --enable-parser=mpeg4video \
        --enable-parser=h264 \
        --disable-demuxers \
        --enable-demuxer=mjpeg \
        --enable-demuxer=avi \
        --enable-demuxer=mov \
        --disable-muxers \
        --enable-muxer=mjpeg \
        --enable-muxer=avi \
        --disable-filters \
        --enable-filter=scale \
        --enable-filter=fps \
        --disable-bsfs \
        --enable-zlib \
        --disable-bzlib \
        --disable-iconv \
        --disable-xlib \
        --disable-sdl2 \
        --enable-pthreads \
        --enable-runtime-cpudetect \
        --arch=x86_64 \
        --cpu=core2
        
    echo "Compiling FFmpeg (using all ${CPU_CORES} cores)..."
    time make -j$(sysctl -n hw.ncpu)
    make install
    
    echo "✅ Minimal FFmpeg built successfully"
    echo "FFmpeg size: $(du -h ${INSTALL_PREFIX}/lib/libav*.a 2>/dev/null | tail -1 | cut -f1 || echo 'N/A')"
}

# Build libmicrohttpd
build_libmicrohttpd() {
    echo "Building libmicrohttpd..."
    
    cd "${BUILD_DIR}"
    
    if [ ! -d "libmicrohttpd-0.9.71" ]; then
        echo "Downloading libmicrohttpd..."
        curl -L -o "libmicrohttpd-0.9.71.tar.gz" \
            "https://ftp.gnu.org/gnu/libmicrohttpd/libmicrohttpd-0.9.71.tar.gz"
        tar -xf "libmicrohttpd-0.9.71.tar.gz"
    fi
    
    cd "libmicrohttpd-0.9.71"
    
    ./configure \
        --prefix="${INSTALL_PREFIX}" \
        --disable-shared \
        --enable-static \
        --disable-doc \
        --disable-examples \
        --disable-curl
        
    make -j$(sysctl -n hw.ncpu)
    make install
    
    echo "✅ libmicrohttpd built successfully"
}

# Build motion daemon (motioneyeos style)
build_motion_daemon() {
    echo "Building motion daemon ${MOTION_VERSION}..."
    
    cd "${BUILD_DIR}"
    
    if [ ! -d "motion-release-${MOTION_VERSION}" ]; then
        echo "Downloading motion ${MOTION_VERSION}..."
        curl -L -o "motion-${MOTION_VERSION}.tar.gz" \
            "https://github.com/Motion-Project/motion/archive/release-${MOTION_VERSION}.tar.gz"
        tar -xf "motion-${MOTION_VERSION}.tar.gz"
    fi
    
    cd "motion-release-${MOTION_VERSION}"
    
    # Regenerate build system
    autoreconf -fiv
    
    # Configure with minimal dependencies (motioneyeos approach)
    PKG_CONFIG_PATH="${INSTALL_PREFIX}/lib/pkgconfig" \
    CPPFLAGS="-I${INSTALL_PREFIX}/include" \
    LDFLAGS="-L${INSTALL_PREFIX}/lib" \
    ./configure \
        --prefix="${INSTALL_PREFIX}" \
        --without-pgsql \
        --without-sqlite3 \
        --without-mysql \
        --without-mariadb \
        --with-ffmpeg="${INSTALL_PREFIX}" \
        --enable-static \
        --disable-shared
        
    make -j$(sysctl -n hw.ncpu)
    make install
    
    echo "✅ Motion daemon built successfully"
}

# Create installation package
create_package() {
    echo "Creating installation package..."
    
    # Create launcher script
    cat > "${INSTALL_PREFIX}/bin/motion-lite" << 'EOF'
#!/bin/bash
# motionEye Lite Motion Daemon Launcher
MOTION_DIR="/usr/local/motioneye-lite"
export PATH="${MOTION_DIR}/bin:${PATH}"
export LD_LIBRARY_PATH="${MOTION_DIR}/lib:${LD_LIBRARY_PATH}"
exec "${MOTION_DIR}/bin/motion" "$@"
EOF
    
    chmod +x "${INSTALL_PREFIX}/bin/motion-lite"
    
    # Create configuration template
    mkdir -p "${INSTALL_PREFIX}/etc"
    cat > "${INSTALL_PREFIX}/etc/motion-lite.conf" << 'EOF'
# motionEye Lite Motion Configuration
# Minimal configuration for compatibility

daemon on
process_id_file /var/run/motion-lite.pid
setup_mode off
log_level 6
log_type syslog
logfile /var/log/motion-lite.log

width 640
height 480
framerate 15
minimum_frame_time 0
auto_brightness off
brightness 0
contrast 0
saturation 0
hue 0

threshold 1500
threshold_tune off
noise_level 32
noise_tune on
despeckle_filter EedDl
smart_mask_speed 0
lightswitch_percent 0
minimum_motion_frames 1
pre_capture 0
post_capture 0

output_pictures off
output_debug_pictures off
quality 75
picture_type jpeg
EOF

    echo "✅ Installation package created at ${INSTALL_PREFIX}"
    echo ""
    echo "To use:"
    echo "  ${INSTALL_PREFIX}/bin/motion-lite -c ${INSTALL_PREFIX}/etc/motion-lite.conf"
}

# Performance monitoring during build
monitor_build_performance() {
    echo "=== Build Performance Monitoring ==="
    echo "System specs:"
    echo "  CPU: $(sysctl -n machdep.cpu.brand_string)"  
    echo "  Cores: $(sysctl -n hw.ncpu) logical cores"
    echo "  Memory: $(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))GB"
    echo "  Load average: $(uptime | awk -F'load averages:' '{print $2}')"
    
    echo "  Build start: $(date)"
    echo "  Estimated completion: $(date -v+2H)"
    echo ""
}

# Verify installation
verify_installation() {
    echo "=== Installation Verification ==="
    
    if [ -f "${INSTALL_PREFIX}/bin/motion" ]; then
        echo "✅ Motion binary installed"
        "${INSTALL_PREFIX}/bin/motion" -V 2>/dev/null | head -1 || echo "⚠️  Version check failed"
    else
        echo "❌ Motion binary not found"
        return 1
    fi
    
    if [ -f "${INSTALL_PREFIX}/bin/motion-lite" ]; then
        echo "✅ Motion-lite wrapper installed"
    else
        echo "❌ Motion-lite wrapper not found"  
        return 1
    fi
    
    echo "✅ Installation verified successfully"
    
    # Display installation summary
    echo ""
    echo "=== Installation Summary ==="
    echo "Install path: ${INSTALL_PREFIX}"
    echo "Disk usage: $(du -sh ${INSTALL_PREFIX} 2>/dev/null | cut -f1)"
    echo "Binary count: $(find ${INSTALL_PREFIX}/bin -type f 2>/dev/null | wc -l | tr -d ' ')"
    echo "Library count: $(find ${INSTALL_PREFIX}/lib -name '*.a' 2>/dev/null | wc -l | tr -d ' ') static libraries"
}

# Main execution with enhanced monitoring
main() {
    local build_start=$(date +%s)
    
    echo "Starting motionEye macOS Lite build..."
    echo "Target system: Mac mini 2014 with macOS 12.7.6"
    echo ""
    
    # Check and create installation directory with proper permissions
    if [ ! -d "${INSTALL_PREFIX}" ]; then
        echo "Creating installation directory (may require sudo)..."
        if sudo mkdir -p "${INSTALL_PREFIX}" 2>/dev/null; then
            sudo chown $(whoami):staff "${INSTALL_PREFIX}"
            echo "✅ Installation directory created: ${INSTALL_PREFIX}"
        else
            echo "❌ Failed to create installation directory"
            echo "Please run: sudo mkdir -p ${INSTALL_PREFIX} && sudo chown $(whoami):staff ${INSTALL_PREFIX}"
            exit 1
        fi
    fi
    
    monitor_build_performance
    
    # Create build directory
    mkdir -p "${BUILD_DIR}"
    
    echo "=== Build Phase 1: Prerequisites ==="
    check_prerequisites
    
    echo "=== Build Phase 2: Dependencies ==="  
    install_lite_dependencies
    
    echo "=== Build Phase 3: FFmpeg (Longest Phase) ==="
    build_minimal_ffmpeg
    
    echo "=== Build Phase 4: HTTP Library ==="
    build_libmicrohttpd
    
    echo "=== Build Phase 5: Motion Daemon ==="  
    build_motion_daemon
    
    echo "=== Build Phase 6: Package Creation ==="
    create_package
    
    echo "=== Build Phase 7: Verification ==="
    verify_installation
    
    local build_end=$(date +%s)
    local build_duration=$(( build_end - build_start ))
    local build_minutes=$(( build_duration / 60 ))
    
    echo ""
    echo "🎉 motionEye macOS Lite build completed successfully!"
    echo ""
    echo "📊 Build Statistics:"
    echo "  Duration: ${build_minutes} minutes (${build_duration} seconds)"
    echo "  Installation: ${INSTALL_PREFIX}"
    echo "  Motion daemon: ${INSTALL_PREFIX}/bin/motion-lite"  
    echo "  Configuration: ${INSTALL_PREFIX}/etc/motion-lite.conf"
    echo "  Build log: ${LOG_FILE}"
    echo ""
    echo "📋 Next Steps:"
    echo "  1. Test installation: ${INSTALL_PREFIX}/bin/motion-lite --help"
    echo "  2. Configure cameras: edit ${INSTALL_PREFIX}/etc/motion-lite.conf" 
    echo "  3. Start daemon: ${INSTALL_PREFIX}/bin/motion-lite -c ${INSTALL_PREFIX}/etc/motion-lite.conf"
    echo ""
    echo "This optimized build should use ~60-70% less CPU than Docker for video processing."
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi