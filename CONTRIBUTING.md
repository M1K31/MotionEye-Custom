# Contributing to MotionEye Custom

Thank you for your interest in contributing to MotionEye Custom! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/MotionEye-Custom.git
   cd MotionEye-Custom
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python3 -m venv motioneye_env
   source motioneye_env/bin/activate  # Linux/macOS
   # or
   motioneye_env\Scripts\activate  # Windows

   # Install in development mode
   pip install -e .
   pip install pytest pytest-cov flake8 black
   ```

3. **Run Tests**
   ```bash
   python -m pytest -v
   ```

## 📋 Development Guidelines

### Code Style
- Follow PEP 8 guidelines
- Use `black` for code formatting: `black motioneye/`
- Use `flake8` for linting: `flake8 motioneye/`
- Maximum line length: 88 characters (black default)

### Testing
- Write tests for new features and bug fixes
- Maintain or improve test coverage
- Run full test suite before submitting PRs
- Add integration tests for significant features

### Commit Messages
Use conventional commit format:
```
type(scope): description

feat(camera): add facial recognition support
fix(server): resolve authentication issue
docs(readme): update installation instructions
test(handlers): add login handler tests
```

## 🔧 Development Environment

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup instructions including:
- Platform-specific dependencies
- Virtual environment setup
- IDE configuration
- Debugging tips

## 📝 Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following our guidelines
   - Add/update tests as needed
   - Update documentation if required

3. **Test Changes**
   ```bash
   # Run tests
   python -m pytest -v
   
   # Check code style
   black --check motioneye/
   flake8 motioneye/
   ```

4. **Submit Pull Request**
   - Use descriptive title and description
   - Reference related issues
   - Include screenshots for UI changes
   - Ensure CI passes

## 🐛 Reporting Issues

### Bug Reports
Include the following information:
- MotionEye version and platform
- Python version
- Steps to reproduce
- Expected vs actual behavior
- Relevant log files
- System specifications

### Feature Requests
- Describe the use case and benefit
- Provide mockups or examples if applicable
- Consider implementation complexity
- Check existing issues for duplicates

## 🏗️ Project Structure

```
MotionEye-Custom/
├── motioneye/           # Main application code
│   ├── handlers/        # Web request handlers
│   ├── scripts/         # Utility scripts
│   ├── static/          # Web assets (CSS, JS)
│   ├── templates/       # HTML templates
│   └── utils/           # Helper utilities
├── tests/               # Test suite
├── docker/              # Docker configuration
├── build/               # Build scripts
├── docs/                # Documentation
└── examples/            # Usage examples
```

## 💡 Areas for Contribution

### High Priority
- 🐛 Bug fixes and stability improvements
- 📝 Documentation improvements
- 🧪 Test coverage expansion
- 🚀 Performance optimizations

### Feature Ideas
- 📱 Mobile app integration
- 🤖 AI/ML enhancements
- 🔌 Additional camera protocols
- 📊 Analytics and reporting
- 🏠 Smart home integrations

### Platform Support
- 🐧 Linux distribution packages
- 🍎 macOS improvements
- 🪟 Windows native support
- 🏗️ ARM platform optimizations

## 📚 Resources

- **Main Documentation:** [README.md](README.md)
- **Development Setup:** [DEVELOPMENT.md](DEVELOPMENT.md)
- **Installation Guide:** [docs/INSTALLATION.md](docs/INSTALLATION.md)
- **New Features:** [NEW_FEATURES.md](NEW_FEATURES.md)

## 💬 Community

- **Discussions:** [GitHub Discussions](https://github.com/M1K31/MotionEye-Custom/discussions)
- **Issues:** [GitHub Issues](https://github.com/M1K31/MotionEye-Custom/issues)
- **Original Project:** [MotionEye Wiki](https://github.com/motioneye-project/motioneye/wiki)

## 📄 License

By contributing, you agree that your contributions will be licensed under the GPL-3.0 License.

---

**Questions?** Feel free to open an issue or start a discussion. We're here to help!
