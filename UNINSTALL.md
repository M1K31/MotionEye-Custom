# Uninstallation Guide

Platform-specific removal steps for MotionEye Custom and its
dependencies.

> ⚠️ **Warning:** Some steps remove configuration and (optionally)
> media files (your recordings and pictures). Back up anything you
> want to keep before proceeding.

---

## Quick reference

| How you installed | How to remove |
|---|---|
| Docker | [Docker](#docker) |
| Linux `pip install motioneye` + apt motion | [Linux](#linux) |
| macOS — `./build/install_macos.sh` (Lite or Standard) | [macOS — Lite / Standard](#macos--lite-or-standard) |
| Dev install (`pip install -e .`) | [Development install](#development-install) |

---

## Docker

```bash
docker stop motioneye
docker rm motioneye

# Remove the image
docker rmi im1k31s/motioneye-custom:latest

# Remove volumes — WARNING: deletes config AND recordings
docker volume rm motioneye-config motioneye-media
```

If you used Compose:

```bash
docker compose down -v   # -v also removes named volumes
```

---

## Linux

A scripted uninstall is provided:

```bash
sudo ./build/uninstall_linux.sh
```

The script:

- Stops and disables the `motioneye` systemd unit
- Uninstalls the Python package via pip
- Removes `/etc/motioneye/` (config)
- *Asks* before removing `/var/lib/motioneye/` (media — recordings,
  snapshots)

### Manual removal

```bash
sudo systemctl stop motioneye
sudo systemctl disable motioneye

pip uninstall motioneye
rm -rf ~/motioneye-env       # if you used a venv
sudo rm -rf /etc/motioneye   # config
sudo rm -rf /var/lib/motioneye   # WARNING: media

# Optional: also remove the Motion daemon and ffmpeg if no other
# apps use them
sudo apt remove --purge motion ffmpeg
```

---

## macOS — Lite or Standard

A scripted uninstall is provided:

```bash
sudo ./build/uninstall_macos.sh
```

The script auto-detects which install you have and removes:

- **Lite**: `/usr/local/motioneye-lite/` (statically-linked Motion +
  ffmpeg + libmicrohttpd, `motioneye-lite` management command if
  installed)
- **Standard**: Homebrew-built `motion` and dependencies
- **System services**: launchd plist
- **Config & runtime**: `/usr/local/etc/motioneye/`, `/var/log/motioneye.log`

### Quick Lite-only removal

If you only have the Lite install:

```bash
sudo launchctl unload /Library/LaunchDaemons/com.motioneye-project.motioneye.plist
sudo rm -f  /Library/LaunchDaemons/com.motioneye-project.motioneye.plist
sudo rm -rf /usr/local/motioneye-lite
sudo rm -f  /usr/local/bin/motioneye-lite     # if installed
```

### Manual Homebrew cleanup (optional)

If you installed Motion or ffmpeg via Homebrew and nothing else
needs them:

```bash
brew uninstall motion ffmpeg
brew autoremove
```

### GUI app, if you packaged one

```bash
sudo rm -rf /Applications/motionEye.app   # if you created a DMG
```

---

## Development install

```bash
# Drop the venv
rm -rf motioneye_env/

# Or if you installed editable into the system Python
pip uninstall motioneye
```

Test config (if you used `MOTIONEYE_CONF_PATH`):

```bash
rm -rf /tmp/motioneye-test
```

---

## Complete cleanup (any platform)

```bash
# Config
sudo rm -rf /etc/motioneye               # Linux
sudo rm -rf /usr/local/etc/motioneye     # macOS standard install

# Media (recordings, snapshots) — WARNING: irreversible
sudo rm -rf /var/lib/motioneye

# Logs
sudo rm -f /var/log/motioneye.log
```

---

## See also

- [Installation Guide](docs/INSTALLATION.md) — to reinstall after
  removal
- [Docker Deployment](docs/DOCKER.md) — Docker-specific operations
