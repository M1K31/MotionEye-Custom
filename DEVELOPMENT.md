# Development Guide

This guide helps developers set up a local development environment for MotionEye Custom.

## 🚀 Quick Development Setup

### Prerequisites

#### All Platforms
- Python 3.9+ (3.11 recommended for best compatibility)
- Git
- C++ compiler toolchain

#### Platform-Specific Requirements

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install build-essential cmake python3-dev pkg-config
sudo apt install libjpeg-dev libpng-dev libtiff-dev libopenblas-dev
```

**macOS:**
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew dependencies
brew install cmake pkg-config openblas libjpeg libpng libtiff
```

**Windows:**
- Install Visual Studio Build Tools
- Use WSL2 with Linux setup (recommended)

### Development Environment Setup

1. **Clone and Setup**
   ```bash
   git clone https://github.com/M1K31/MotionEye-Custom.git
   cd MotionEye-Custom
   
   # Create virtual environment
   python3 -m venv motioneye_env
   source motioneye_env/bin/activate  # Linux/macOS
   # motioneye_env\Scripts\activate  # Windows
   
   # Upgrade core tools
   pip install --upgrade pip setuptools wheel
   ```

2. **Install Dependencies**
   ```bash
   # Install in development mode
   pip install -e .
   
   # Install development tools
   pip install pytest pytest-cov black flake8 pre-commit
   
   # Install pre-commit hooks
   pre-commit install
   ```

3. **Verify Installation**
   ```bash
   # Run test suite
   python -m pytest -v
   
   # Start development server
   python -m motioneye.meyectl startserver
   ```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=motioneye --cov-report=html

# Run specific test categories
python -m pytest test_integration.py       # Integration tests
python -m pytest test_motioneye_lite.py   # MotionEye Lite tests
python -m pytest tests/                   # Unit tests

# Run tests with verbose output
python -m pytest -v -s
```

### Test Categories
- **Unit Tests:** `tests/` - Individual component testing
- **Integration Tests:** `test_integration.py` - System-wide functionality
- **Lite Tests:** `test_motioneye_lite.py` - MotionEye Lite specific features

### Writing Tests
```python
import pytest
from motioneye import config

def test_config_loading():
    """Test configuration loading functionality."""
    # Test implementation
    assert config.load_default() is not None
```

## 🔧 Code Quality

### Code Formatting
```bash
# Format code with Black
black motioneye/ tests/

# Check formatting
black --check motioneye/
```

### Linting
```bash
# Run flake8 linting
flake8 motioneye/ tests/

# Fix common issues automatically
autopep8 --in-place --recursive motioneye/
```

### Pre-commit Hooks
Automatically run quality checks before commits:
```bash
pre-commit install
# Now hooks run automatically on git commit
```

## 🏗️ Project Architecture

### Directory Structure
```
motioneye/
├── __init__.py          # Package initialization
├── config.py            # Configuration management  
├── server.py            # Web server and handlers
├── monitor.py           # Camera monitoring
├── motionctl.py         # Motion daemon control
├── handlers/            # Web request handlers
├── scripts/             # Utility scripts
├── static/              # Web assets (CSS, JS, images)
├── templates/           # Jinja2 HTML templates
└── utils/               # Helper utilities
```

### Key Components
- **Server:** Tornado-based web application
- **Config:** YAML-based configuration system
- **Monitor:** Camera and motion detection management  
- **Handlers:** HTTP request processing
- **Templates:** Web interface rendering

### Adding New Features
1. **Backend Logic:** Add to appropriate module in `motioneye/`
2. **Web Interface:** Create handler in `handlers/` and template in `templates/`
3. **API Endpoints:** Extend handlers with JSON responses
4. **Tests:** Add unit tests in `tests/` and integration tests as needed

## 🍎 macOS Development (MotionEye Lite)

For high-performance macOS development using embedded binaries:

### Lite Development Setup
```bash
# Build and install Lite version
./build/install_macos.sh

# Test Lite installation
python test_motioneye_lite.py

# Monitor performance
/opt/motioneye-lite/bin/motion -h
```

### Lite Development Workflow
1. **Modify Build Scripts:** Edit `build/build_motion_macos.sh`
2. **Test Components:** Run Lite-specific tests
3. **Performance Validation:** Compare against Docker performance  
4. **Update Documentation:** Modify Lite-specific docs

### Key Lite Files
- `build/build_motion_macos.sh` - Main build script
- `build/install_macos.sh` - Installation script  
- `test_motioneye_lite.py` - Integration tests
- `docs/MOTIONEYE_LITE.md` - Technical documentation

## 🐳 Docker Development

### Development with Docker
```bash
# Build development image
docker build -f docker/Dockerfile -t motioneye-dev .

# Run with development setup
docker run -it --rm \
  -p 8765:8765 \
  -v $(pwd):/app \
  motioneye-dev bash

# Inside container
python -m pytest
python -m motioneye.meyectl startserver
```

### Multi-platform Testing
```bash
# Test ARM64 build
docker buildx build --platform linux/arm64 -t motioneye-arm64 .

# Test AMD64 build  
docker buildx build --platform linux/amd64 -t motioneye-amd64 .
```

## 🔍 Debugging

### Development Server
```bash
# Start with debug logging
export DEBUG=1
python -m motioneye.meyectl startserver --debug

# Enable verbose logging
export MOTIONEYE_LOG_LEVEL=DEBUG
```

### Common Issues

**Import Errors:**
```bash
# Ensure virtual environment is activated
source motioneye_env/bin/activate

# Reinstall in development mode
pip install -e .
```

**Camera Detection Issues:**
```bash
# List available video devices (Linux)
ls -la /dev/video*

# Test camera access
v4l2-ctl --list-devices  # Linux
system_profiler SPCameraDataType  # macOS
```

**Performance Issues:**
```bash
# Profile application
python -m cProfile -o profile.stats -m motioneye.meyectl startserver

# Analyze with py-spy (install separately)
py-spy record -o profile.svg -d 60 -s -- python -m motioneye.meyectl startserver
```

## 📊 Performance Testing

### Benchmarking
```bash
# Memory usage monitoring
python -m memory_profiler motioneye/server.py

# Load testing with multiple cameras
# Configure test cameras in test environment
```

### MotionEye Lite Performance
- Target: 60-70% better performance than Docker
- Monitor: CPU usage, memory consumption, latency
- Compare: Native vs Docker vs traditional installation methods

## 🚀 Release Process

### Preparation
1. Update version in `setup.py` and `pyproject.toml`
2. Update `NEW_FEATURES.md` and `CHANGELOG.md`
3. Run full test suite across platforms
4. Update documentation

### Testing
```bash
# Full test suite
python -m pytest -v --cov=motioneye

# Integration tests
python test_integration.py

# Platform-specific tests
python test_motioneye_lite.py  # macOS
```

### Building
```bash
# Build source distribution
python setup.py sdist

# Build wheel
python setup.py bdist_wheel

# Test installation from built package
pip install dist/motioneye-*.whl
```

## 💡 Contributing Tips

1. **Start Small:** Begin with bug fixes or documentation improvements
2. **Follow Patterns:** Study existing code for style and architecture patterns
3. **Test Thoroughly:** Add tests for new features and edge cases
4. **Document Changes:** Update relevant documentation
5. **Performance Conscious:** Consider impact on resource usage

## 📚 Additional Resources

- **API Documentation:** Generate with `pydoc` or `sphinx`
- **Original Project:** [MotionEye Wiki](https://github.com/motioneye-project/motioneye/wiki)
- **Motion Documentation:** [Motion Project](https://motion-project.github.io/)
- **Tornado Documentation:** [Tornado Web Server](https://www.tornadoweb.org/)

## 🆘 Getting Help

- **Issues:** Report bugs and request features on GitHub Issues
- **Discussions:** Join conversations on GitHub Discussions  
- **Code Review:** Submit PRs for collaborative development
- **Documentation:** Improve guides and help others learn

Remember: Good development practices include regular commits, meaningful commit messages, and thorough testing!