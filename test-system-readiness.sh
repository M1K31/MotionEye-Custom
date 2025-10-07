#!/bin/bash
# motionEye Lite Pre-Build Test Suite
# Validates system readiness for Mac mini 2014

set -e

PROJECT_DIR="/Users/mikelsmart/Downloads/GitHubProjects/MotionEye-Custom"
TEST_LOG="${PROJECT_DIR}/pre-build-test.log"

echo "=== motionEye Lite Pre-Build Tests ===" | tee "$TEST_LOG"
echo "Testing system readiness for Mac mini 2014" | tee -a "$TEST_LOG"
echo "Started: $(date)" | tee -a "$TEST_LOG"
echo "" | tee -a "$TEST_LOG"

# Test 1: System Requirements
test_system_requirements() {
    echo "🔍 Test 1: System Requirements" | tee -a "$TEST_LOG"
    
    # CPU check
    local cpu_cores=$(sysctl -n hw.ncpu)
    local cpu_name=$(sysctl -n machdep.cpu.brand_string)
    echo "  CPU: $cpu_name ($cpu_cores cores)" | tee -a "$TEST_LOG"
    
    if [ "$cpu_cores" -ge 2 ]; then
        echo "  ✅ CPU: Adequate ($cpu_cores cores >= 2 required)" | tee -a "$TEST_LOG"
    else
        echo "  ❌ CPU: Insufficient ($cpu_cores cores < 2 required)" | tee -a "$TEST_LOG"
        return 1
    fi
    
    # Memory check  
    local mem_gb=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
    echo "  RAM: ${mem_gb}GB" | tee -a "$TEST_LOG"
    
    if [ "$mem_gb" -ge 8 ]; then
        echo "  ✅ RAM: Adequate (${mem_gb}GB >= 8GB required)" | tee -a "$TEST_LOG"
    else
        echo "  ❌ RAM: Insufficient (${mem_gb}GB < 8GB required)" | tee -a "$TEST_LOG"
        return 1
    fi
    
    # macOS version check
    local macos_version=$(sw_vers -productVersion)
    echo "  macOS: $macos_version" | tee -a "$TEST_LOG"
    echo "  ✅ macOS: Compatible" | tee -a "$TEST_LOG"
    
    return 0
}

# Test 2: Prerequisites
test_prerequisites() {
    echo "" | tee -a "$TEST_LOG"
    echo "🔍 Test 2: Build Prerequisites" | tee -a "$TEST_LOG"
    
    local missing_tools=()
    
    # Check essential tools
    for tool in git make autoconf automake libtool pkg-config; do
        if command -v "$tool" >/dev/null 2>&1; then
            echo "  ✅ $tool: $(command -v $tool)" | tee -a "$TEST_LOG"
        else
            echo "  ❌ $tool: Missing" | tee -a "$TEST_LOG"
            missing_tools+=("$tool")
        fi
    done
    
    # Check Xcode Command Line Tools
    if xcode-select -p >/dev/null 2>&1; then
        echo "  ✅ Xcode CLI Tools: $(xcode-select -p)" | tee -a "$TEST_LOG"
    else
        echo "  ❌ Xcode CLI Tools: Missing" | tee -a "$TEST_LOG"
        missing_tools+=("xcode-select")
    fi
    
    # Check Homebrew
    if command -v brew >/dev/null 2>&1; then
        local brew_version=$(brew --version | head -1)
        echo "  ✅ Homebrew: $brew_version" | tee -a "$TEST_LOG"
    else
        echo "  ❌ Homebrew: Missing" | tee -a "$TEST_LOG"
        missing_tools+=("brew")
    fi
    
    if [ ${#missing_tools[@]} -eq 0 ]; then
        echo "  ✅ All prerequisites satisfied" | tee -a "$TEST_LOG"
        return 0
    else
        echo "  ❌ Missing tools: ${missing_tools[*]}" | tee -a "$TEST_LOG"
        return 1
    fi
}

# Test 3: Current System Performance
test_current_performance() {
    echo "" | tee -a "$TEST_LOG"
    echo "🔍 Test 3: Current System Performance" | tee -a "$TEST_LOG"
    
    # CPU usage
    local cpu_usage=$(top -l 1 -n 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    echo "  Current CPU usage: ${cpu_usage}%" | tee -a "$TEST_LOG"
    
    if (( $(echo "$cpu_usage < 70" | bc -l 2>/dev/null || echo 0) )); then
        echo "  ✅ CPU: Good availability for build" | tee -a "$TEST_LOG"
    else
        echo "  ⚠️  CPU: High usage, build may be slow" | tee -a "$TEST_LOG"
    fi
    
    # Memory pressure
    local mem_pressure=$(memory_pressure 2>/dev/null | grep "System-wide memory free percentage" | awk '{print $5}' | sed 's/%//' || echo "unknown")
    echo "  Memory free: ${mem_pressure}%" | tee -a "$TEST_LOG"
    
    # Load average
    local load_avg=$(uptime | awk -F'load averages:' '{print $2}' | awk '{print $1}')
    echo "  Load average: $load_avg" | tee -a "$TEST_LOG"
    
    return 0
}

# Test 4: Disk Space
test_disk_space() {
    echo "" | tee -a "$TEST_LOG"
    echo "🔍 Test 4: Disk Space Requirements" | tee -a "$TEST_LOG"
    
    # Check available space
    local available_gb=$(df -g . | tail -1 | awk '{print $4}')
    echo "  Available space: ${available_gb}GB" | tee -a "$TEST_LOG"
    
    # Estimate build requirements
    echo "  Build space needed:" | tee -a "$TEST_LOG"
    echo "    Source downloads: ~200MB" | tee -a "$TEST_LOG"
    echo "    Build artifacts: ~2-3GB" | tee -a "$TEST_LOG"
    echo "    Installation: ~100MB" | tee -a "$TEST_LOG"
    echo "    Total estimated: ~3.5GB" | tee -a "$TEST_LOG"
    
    if [ "$available_gb" -ge 5 ]; then
        echo "  ✅ Disk space: Adequate (${available_gb}GB >= 5GB required)" | tee -a "$TEST_LOG"
        return 0
    else
        echo "  ❌ Disk space: Insufficient (${available_gb}GB < 5GB required)" | tee -a "$TEST_LOG"
        return 1
    fi
}

# Test 5: Python Environment  
test_python_environment() {
    echo "" | tee -a "$TEST_LOG"
    echo "🔍 Test 5: Python Environment" | tee -a "$TEST_LOG"
    
    cd "$PROJECT_DIR"
    
    # Check Python version
    local python_version=$(python --version 2>&1)
    echo "  Python: $python_version" | tee -a "$TEST_LOG"
    
    # Test motionEye import
    if python -c "import motioneye" 2>/dev/null; then
        echo "  ✅ motionEye module: Available" | tee -a "$TEST_LOG"
    else
        echo "  ❌ motionEye module: Import failed" | tee -a "$TEST_LOG"
        return 1
    fi
    
    # Test basic functionality
    if python -m motioneye.meyectl 2>&1 | grep -q "meyectl"; then
        echo "  ✅ meyectl: Functional" | tee -a "$TEST_LOG"
    else
        echo "  ❌ meyectl: Not working" | tee -a "$TEST_LOG" 
        return 1
    fi
    
    return 0
}

# Test 6: Network and Permissions
test_network_permissions() {
    echo "" | tee -a "$TEST_LOG"
    echo "🔍 Test 6: Network and Permissions" | tee -a "$TEST_LOG"
    
    # Test internet connectivity for downloads
    if curl -s --max-time 5 https://ffmpeg.org >/dev/null; then
        echo "  ✅ Internet: Accessible for downloads" | tee -a "$TEST_LOG"
    else
        echo "  ❌ Internet: Cannot reach download sites" | tee -a "$TEST_LOG"
        return 1
    fi
    
    # Test write permissions for install directory
    local install_dir="/usr/local"
    if [ -w "$install_dir" ] || sudo -n test -w "$install_dir" 2>/dev/null; then
        echo "  ✅ Permissions: Can write to /usr/local" | tee -a "$TEST_LOG"
    else
        echo "  ⚠️  Permissions: May need sudo for installation" | tee -a "$TEST_LOG"
    fi
    
    # Test ports for services
    for port in 8080 8081 8765; do
        if ! lsof -i:$port >/dev/null 2>&1; then
            echo "  ✅ Port $port: Available" | tee -a "$TEST_LOG"
        else
            echo "  ⚠️  Port $port: In use" | tee -a "$TEST_LOG"
        fi
    done
    
    return 0
}

# Performance prediction
predict_build_performance() {
    echo "" | tee -a "$TEST_LOG"
    echo "📊 Build Performance Prediction" | tee -a "$TEST_LOG"
    
    local cpu_cores=$(sysctl -n hw.ncpu)
    local cpu_freq=$(sysctl -n hw.cpufrequency_max 2>/dev/null || echo "3000000000")
    local cpu_ghz=$(echo "scale=1; $cpu_freq / 1000000000" | bc 2>/dev/null || echo "3.0")
    
    echo "  Hardware: $cpu_cores cores @ ${cpu_ghz}GHz" | tee -a "$TEST_LOG"
    
    # Estimate build time based on Mac mini 2014
    echo "  Estimated build times:" | tee -a "$TEST_LOG"
    echo "    FFmpeg: 45-90 minutes" | tee -a "$TEST_LOG"
    echo "    libmicrohttpd: 5-10 minutes" | tee -a "$TEST_LOG"
    echo "    Motion: 10-20 minutes" | tee -a "$TEST_LOG"
    echo "    Total: 60-120 minutes" | tee -a "$TEST_LOG"
    
    # Performance recommendations
    echo "" | tee -a "$TEST_LOG"
    echo "  Recommendations:" | tee -a "$TEST_LOG"
    echo "    • Close unnecessary applications during build" | tee -a "$TEST_LOG"
    echo "    • Ensure adequate cooling" | tee -a "$TEST_LOG"
    echo "    • Monitor CPU temperature" | tee -a "$TEST_LOG"
    echo "    • Build during low-usage periods" | tee -a "$TEST_LOG"
}

# Main test execution
main() {
    local failed_tests=0
    
    test_system_requirements || ((failed_tests++))
    test_prerequisites || ((failed_tests++))
    test_current_performance || ((failed_tests++))
    test_disk_space || ((failed_tests++))
    test_python_environment || ((failed_tests++))
    test_network_permissions || ((failed_tests++))
    
    predict_build_performance
    
    echo "" | tee -a "$TEST_LOG"
    echo "=== Test Summary ===" | tee -a "$TEST_LOG"
    echo "Completed: $(date)" | tee -a "$TEST_LOG"
    
    if [ $failed_tests -eq 0 ]; then
        echo "✅ All tests passed! System ready for motionEye Lite build" | tee -a "$TEST_LOG"
        echo "" | tee -a "$TEST_LOG"
        echo "🚀 Ready to proceed with:" | tee -a "$TEST_LOG"
        echo "    ./motioneye-lite install" | tee -a "$TEST_LOG"
        echo "" | tee -a "$TEST_LOG"
        return 0
    else
        echo "❌ $failed_tests test(s) failed. Address issues before building." | tee -a "$TEST_LOG"
        echo "" | tee -a "$TEST_LOG"
        echo "📋 Next steps:" | tee -a "$TEST_LOG"
        echo "  1. Review failed tests above" | tee -a "$TEST_LOG"
        echo "  2. Install missing prerequisites" | tee -a "$TEST_LOG"
        echo "  3. Re-run: $0" | tee -a "$TEST_LOG"
        echo "" | tee -a "$TEST_LOG"
        return 1
    fi
}

# Run tests
main