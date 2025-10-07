## macOS: quick venv setup (CMake, Homebrew deps, venv recreate)

This project uses native extensions (OpenCV, dlib) that often need system build tools on macOS. Follow these steps to create a working Python virtualenv and install the project.

1) Install prerequisites

Install Xcode Command Line Tools (if not already installed):

```zsh
xcode-select --install
```

Install Homebrew (if you don't have it):

```zsh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2) Install required system packages via Homebrew

These packages are commonly needed to build OpenCV and dlib from source.

```zsh
# core build tools
brew install cmake pkg-config
# math & image libs
brew install openblas libjpeg libpng libtiff
# optional helpful libs for some opencv features
brew install libomp boost
```

3) Recreate the virtualenv (clean, recommended)

```zsh
# from the repo root
rm -rf motioneye_env
python3 -m venv motioneye_env
source motioneye_env/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

4) Install the project and test dependencies

```zsh
# install the package (this will build necessary wheels)
python -m pip install .
# install test runner
python -m pip install pytest
# run tests
python -m pytest -q
```

Notes and troubleshooting

- Building `opencv-python` and `dlib` can take several minutes and requires CMake and a working compiler toolchain. If a build fails with missing headers like `emmintrin.h` or other compiler errors, ensure Xcode CLT is installed (step 1) and that Homebrew packages above are present.
- If you run into incompatibilities with very new Python versions (e.g. 3.13+), consider using Python 3.11/3.12 (pyenv or Homebrew) because some packages provide prebuilt wheels for those versions.
- If you'd rather avoid local builds, use Docker for a reproducible Linux environment (see `docker/Dockerfile` and `docker/docker-compose.yml`).

I have included an automation script `setup_dev.sh` to run these steps on macOS. If you prefer CI, there's also a GitHub Actions workflow that runs tests on Linux and macOS.

CI caching note

- The GitHub Actions workflow caches a `.venv` directory and pip's cache to speed up repeated runs. If you change Python versions or hit unexpected dependency issues after a cache restore, re-run `rm -rf .venv` locally (or in CI by changing the cache key) to force a clean install.
