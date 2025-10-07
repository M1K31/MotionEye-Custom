# Uninstallation Guide

This guide provides platform-specific instructions for uninstalling motionEye and its dependencies from your system.

**⚠️ Warning:** These scripts will remove configuration files. Some steps will also offer to remove all media files (your recordings and pictures). Please back up any important data before proceeding.

## Platform-Specific Considerations

**Docker Installations:** Simply remove containers and images:
```bash
docker stop $(docker ps -q --filter ancestor=motioneye-local)
docker rmi motioneye-local
```

**Development Installations:** Uninstall via pip:
```bash
pip uninstall motioneye
```

**System Installations:** Use platform-specific scripts below.

## Linux (Debian/Ubuntu)

An `uninstall_linux.sh` script is provided in the `build` directory to automate the uninstallation process.

### To Uninstall:
1.  Navigate to the root of this repository.
2.  Run the uninstallation script with `sudo`:
    ```sh
    sudo ./build/uninstall_linux.sh
    ```
3.  The script will guide you through the process.

## macOS

An `uninstall_macos.sh` script is provided in the `build` directory to automate the uninstallation process.

### System Installation (Standard or Lite):
1.  Navigate to the root of this repository
2.  Run the comprehensive uninstallation script with `sudo`:
    ```sh
    sudo ./build/uninstall_macos.sh
    ```
3.  The script automatically detects and removes:
    - **motionEye Lite**: Complete embedded build (`/usr/local/motioneye-lite/`) with:
      - Motion 4.3.1 binary and FFmpeg 4.3.1 libraries 
      - `motioneye-lite` management command
      - All statically-linked components and optimizations
    - **Standard Installation**: Homebrew-built motion daemon and dependencies
    - **System Services**: Background service (`launchd` configuration)  
    - **Configuration**: System-level configuration files and logs
    - **Runtime Data**: Log files and runtime directories

### Quick motionEye Lite Removal:
For Lite installations only, you can also use:
```sh
motioneye-lite stop      # Stop the service
sudo rm -rf /usr/local/motioneye-lite/
sudo rm -f /usr/local/bin/motioneye-lite
```

### Manual Cleanup (if needed):
4.  Remove any remaining GUI application: drag `motionEye.app` from `/Applications` to Trash
5.  Clean up Homebrew dependencies (optional):
    ```sh
    brew uninstall motion ffmpeg
    brew autoremove
    ```

### Development Environment:
For development installations, simply run:
```bash
pip uninstall motioneye
rm -rf motioneye_env/  # if using virtual environment
```
5.  The script will offer to remove your media files separately.
